import functools
import json
import pathlib
import shutil
import threading
import uuid
from collections.abc import Callable
from typing import BinaryIO, Literal, TextIO

from loguru import logger
from pydantic import BaseModel, JsonValue, ValidationError

from consortium.server.exceptions.object_exceptions.repository_object_exceptions import (
    RepositoryDirectoryDoesNotExistError,
    RepositoryFileDoesNotExistError,
)
from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    RepositoryMetadataFileEncodingError,
    RepositoryMetadataFileJSONError,
    RepositoryMetadataFileResourceDataSchemaError,
    RepositoryMetadataFileSchemaError,
    RepositoryMetadataFileSystemError,
    ResourceAlreadyExistsError,
    ResourceIDReservationNotFoundError,
    ResourceNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.models.repository_models import (
    PersistentRepositoryMetadataModel,
    PersistentRepositoryResourceModel,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)
from consortium.server.utils import (
    atomic_write_bytes,
    format_validation_error,
    normalize_uuid,
    wrap_filesystem_errors,
)

# Resource objects report placement failures separately from metadata I/O failures.
# Rollback preserves the original failure and logs any secondary recovery failure.
_wrap_metadata_filesystem_errors = functools.partial(
    wrap_filesystem_errors,
    RepositoryMetadataFileSystemError,
)


class RepositoryService:
    def __init__(
        self,
        repository_directory_path: pathlib.Path,
        data_model: type[BaseModel] | None = None,
    ):
        self.repository_directory_path = repository_directory_path
        self._data_model = data_model
        self._lock = threading.Lock()
        self._resources = {}
        self._reserved_resource_ids = set()
        self._repository_metadata_file_path = (
            repository_directory_path / ".repository.json"
        )
        # Several repository services run at once (one each for artifacts, assets and
        # payloads), so the logger is named for the directory it manages rather than for
        # the class, which would make all of them indistinguishable in the log.
        self._logger = logger.bind(
            logger_name=f"{self} ({repository_directory_path.name})",
            logger_type=LoggerType.SERVICE_LOGGER,
        )

    def __str__(self) -> str:
        return "Repository Service"

    def __repr__(self) -> str:
        return f"RepositoryService(repository_directory_path={self.repository_directory_path!r})"

    def load_repository_metadata(self) -> None:
        """Loads repository resource metadata from the repository metadata JSON file on disk.

        Replaces the current index with the validated metadata. If the metadata file
        does not exist, an empty index is persisted. Missing-on-disk records are warned
        about and dropped, then the repaired metadata is saved. If that save fails,
        survivors remain available in memory and the next save retries persistence.
        Corrupt metadata leaves the previous index untouched. Unindexed files and
        partially deleted directory contents are not reconciled.

        Raises:
            RepositoryMetadataFileEncodingError: If the metadata file's bytes are
                not valid UTF-8.
            RepositoryMetadataFileJSONError: If the metadata file contains
                invalid JSON.
            RepositoryMetadataFileSchemaError: If the metadata file does not
                follow the expected schema.
            RepositoryMetadataFileResourceDataSchemaError: If a `data` field in the
                metadata file fails validation against the repository's `data_model`.
                Only raised when the repository was constructed with a `data_model`.
            RepositoryMetadataFileSystemError: If the metadata file cannot be read or
                initialized, or a recorded resource path cannot be inspected.
        """
        with self._lock:
            if not self._repository_metadata_file_path.exists():
                previous_resources = self._resources
                self._resources = {}
                try:
                    self._save_repository_metadata_locked()
                except Exception:
                    self._resources = previous_resources
                    raise
                return

            # Decode separately so invalid UTF-8 remains distinct from invalid JSON.
            with _wrap_metadata_filesystem_errors(
                operation="read the repository metadata file",
                path=self._repository_metadata_file_path,
            ):
                try:
                    with self._repository_metadata_file_path.open(
                        mode="r", encoding="utf-8"
                    ) as file:
                        repository_metadata_file_content = file.read()
                except UnicodeDecodeError as exc:
                    raise RepositoryMetadataFileEncodingError(
                        path=str(self.repository_directory_path),
                        underlying_error=f"{type(exc).__name__}: {exc}",
                    ) from None

            try:
                repository_metadata_json = json.loads(repository_metadata_file_content)
            except json.JSONDecodeError:
                raise RepositoryMetadataFileJSONError(
                    path=str(self.repository_directory_path),
                ) from None

            # Validate IDs, entry shapes and timestamps before reconstructing resources.
            try:
                repository_metadata = PersistentRepositoryMetadataModel.model_validate(
                    repository_metadata_json,
                ).root
            except ValidationError as exc:
                raise RepositoryMetadataFileSchemaError(
                    path=str(self.repository_directory_path),
                    validation_error_message=format_validation_error(exc),
                ) from None

            # Attribute data-model failures to their resource, even if its bytes are gone.
            if self._data_model is not None:
                for resource_id, resource_metadata in repository_metadata.items():
                    try:
                        self._data_model.model_validate(resource_metadata.data)
                    except ValidationError as exc:
                        raise RepositoryMetadataFileResourceDataSchemaError(
                            path=str(self.repository_directory_path),
                            resource_id=str(resource_id),
                            validation_error_message=format_validation_error(exc),
                        ) from None

            # Stage the replacement so validation failures preserve the live index.
            unsynced_resource_ids = []
            resource_id_to_path_and_metadata_map: dict[
                str, tuple[pathlib.Path, PersistentRepositoryResourceModel]
            ] = {}
            for resource_metadata in repository_metadata.values():
                resource_id = str(resource_metadata.resource_id)
                # Storage paths use the resource ID, never the display name.
                resource_path = self.repository_directory_path / resource_id
                with _wrap_metadata_filesystem_errors(
                    operation="inspect the repository resource", path=resource_path
                ):
                    try:
                        resource_path.stat()
                    except FileNotFoundError:
                        unsynced_resource_ids.append(resource_id)
                        self._logger.warning(
                            "Dropping missing repository resource '{}' at '{}'",
                            resource_id,
                            resource_path,
                        )
                        continue
                resource_id_to_path_and_metadata_map[resource_id] = (
                    resource_path,
                    resource_metadata,
                )

            resources = {}
            for resource_id, (
                resource_path,
                resource_metadata,
            ) in resource_id_to_path_and_metadata_map.items():
                if resource_metadata.is_directory:
                    resource = RepositoryDirectory(
                        path=resource_path,
                    )
                else:
                    resource = RepositoryFile(
                        path=resource_path,
                    )

                # Override the ID generated by the constructor with the persisted ID.
                resource.resource_id = resource_id
                # The unnamed fallback must use the persisted ID too.
                resource.name = (
                    resource_metadata.name if resource_metadata.name else resource_id
                )
                resource.description = resource_metadata.description
                resource.datetime_created = resource_metadata.datetime_created
                resource.is_directory = resource_metadata.is_directory
                resource.data = resource_metadata.data

                resources[resource.resource_id] = resource

            self._resources = resources
            if unsynced_resource_ids:
                try:
                    self._save_repository_metadata_locked()
                except Exception:
                    self._logger.exception(
                        "Failed to persist reconciled repository metadata at '{}'; "
                        "surviving resources remain available in memory",
                        self._repository_metadata_file_path,
                    )

    def save_repository_metadata(self) -> None:
        """Writes the current in-memory repository resource metadata to disk as JSON.

        Raises:
            RepositoryResourceFileSystemError: If a tracked resource's `size` or
                `datetime_modified` cannot be read from disk while its metadata
                representation is being built.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk.
            TypeError: If a tracked resource's `data` is not JSON serializable. This is
                deliberately left unwrapped: it means a caller associated data with a
                resource that cannot be persisted, which is a defect in that caller
                rather than a condition the repository can report on and continue past.
        """
        with self._lock:
            self._save_repository_metadata_locked()

    def _save_repository_metadata_locked(self) -> None:
        # The caller holds _lock through serialization, including directory traversal.
        repository_metadata_json = {
            resource_id: resource.to_json()
            for resource_id, resource in self._resources.items()
        }
        with _wrap_metadata_filesystem_errors(
            operation="write the repository metadata file",
            path=self._repository_metadata_file_path,
        ):
            # ASCII JSON encodes losslessly; atomic replacement preserves the old index
            # if the write fails before publication.
            data = json.dumps(repository_metadata_json, indent=4)
            atomic_write_bytes(
                self._repository_metadata_file_path, data.encode("utf-8")
            )

    def reserve_resource_id(self) -> uuid.UUID:
        """Generates and reserves a resource ID to be claimed during resource creation.

        The reserved ID must be passed as `resource_id` to `create_file` or
        `create_directory`. This allows the caller to know the resource ID before the
        file or directory is created (e.g., to embed the ID in the file content).

        Returns:
            The reserved resource ID.
        """
        with self._lock:
            resource_id = uuid.uuid4()
            self._reserved_resource_ids.add(str(resource_id))
            return resource_id

    def _create_resource[Resource: RepositoryFile | RepositoryDirectory](
        self,
        factory: Callable[[pathlib.Path], Resource],
        resource_id: str | uuid.UUID | None,
        move_source: pathlib.Path | None = None,
    ) -> Resource:
        with self._lock:
            if resource_id is not None:
                resource_id_str = normalize_uuid(resource_id)
                if resource_id_str not in self._reserved_resource_ids:
                    raise ResourceIDReservationNotFoundError(
                        resource_id=resource_id_str
                    )
                unique_resource_id = uuid.UUID(resource_id_str)
            else:
                unique_resource_id = uuid.uuid4()
                resource_id_str = str(unique_resource_id)

            destination = self.repository_directory_path / resource_id_str
            # A previous failed rollback may have retained the only copy here.
            if destination.exists() or destination.is_symlink():
                raise ResourceAlreadyExistsError(resource_id=resource_id_str)
            if move_source is not None:
                move_source = move_source.absolute()
            self._reserved_resource_ids.discard(resource_id_str)
            resource = None
            try:
                resource = factory(destination)
                resource.resource_id = unique_resource_id
                self._resources[resource_id_str] = resource
                self._save_repository_metadata_locked()
            except Exception:
                self._resources.pop(resource_id_str, None)
                if resource_id is not None:
                    self._reserved_resource_ids.add(resource_id_str)
                self._rollback_created_resource_locked(
                    resource, destination, move_source
                )
                raise
            return resource

    def _rollback_created_resource_locked(
        self,
        resource: RepositoryFile | RepositoryDirectory | None,
        destination: pathlib.Path,
        move_source: pathlib.Path | None,
    ) -> None:
        if move_source is not None:
            try:
                if not (destination.exists() or destination.is_symlink()):
                    return
                if move_source.exists() or move_source.is_symlink():
                    raise FileExistsError(f"Source path is occupied: {move_source}")
                shutil.move(str(destination), move_source)
            except Exception:
                self._logger.exception(
                    "Failed to move repository resource back from '{}' to '{}'; "
                    "retaining the repository destination to preserve its bytes",
                    destination,
                    move_source,
                )
            return

        if resource is None:
            # Placement may have failed partway through; no complete resource to undo.
            self._logger.warning(
                "Resource placement failed at '{}'; partial unindexed bytes may remain",
                destination,
            )
            return
        try:
            resource.delete()
        except RepositoryFileDoesNotExistError, RepositoryDirectoryDoesNotExistError:
            pass
        except Exception:
            self._logger.exception(
                "Failed to remove unindexed repository resource at '{}' during rollback",
                destination,
            )

    def create_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ) -> RepositoryFile:
        """Creates and persists a new file resource in the repository.

        The file is stored on disk under its resource ID alone, with no extension.
        Metadata is persisted after creation. A failure removes the new record,
        restores an explicit reservation and attempts to delete the new bytes.
        Failed cleanup can leave unindexed bytes; crashes are not reconciled atomically.

        Args:
            content: The file content to write.
            name: A human-readable name for the file, recorded exactly as given and used
                as the name the resource is served and downloaded under. When `None`, the
                resource UUID is used as the name.
            description: An optional description for the file.
            resource_id: A previously reserved ID to assign to
                this resource. When `None`, a new ID is generated automatically.
            data: Optional additional metadata to associate with
                the file resource.

        Returns:
            The newly created repository file resource.

        Raises:
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
            ResourceAlreadyExistsError: If the destination is already occupied, such as
                by bytes retained after a failed rollback.
            RepositoryResourceFileSystemError: If the file cannot be written to disk.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk.
            UnicodeDecodeError: If `content` is a text stream carrying content that
                cannot be decoded. Left unwrapped as it describes the content the caller
                supplied rather than a failure of the repository itself.
        """
        return self._create_resource(
            factory=lambda destination: RepositoryFile.create(
                path=destination,
                content=content,
                name=name if name else destination.name,
                description=description,
                data=data,
            ),
            resource_id=resource_id,
        )

    def add_file(
        self,
        path: pathlib.Path | str,
        copy: bool = False,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ) -> RepositoryFile:
        """Registers an existing file on disk into the repository.

        Unlike `create_file`, no new file is written. The file at `path` is moved
        (or copied when `copy=True`) into the repository directory under its resource ID
        alone, with no extension, and registered as a resource. Metadata is persisted
        after registration. On failure, the record is removed and an explicit
        reservation is restored. Copies are deleted on a best-effort basis; moves
        are moved back. If the source path is occupied or move-back fails, the bytes
        are retained in the repository and both paths are logged. Partial placement,
        failed cleanup and crashes can leave unindexed bytes.

        Args:
            path: Path to the existing file to register.
            copy: When `False` (default) the source file is moved into the
                repository. When `True` the source file is copied and the original
                is left in place.
            resource_id: A previously reserved ID to
                assign to this resource. When `None`, a new ID is generated.
            name: A human-readable name for the file, recorded exactly as given and used
                as the name the resource is served and downloaded under. Never affects
                how the file is stored on disk. When `None`, the original filename is
                used.
            description: An optional description for the file.
            data: Optional additional metadata to associate with
                the file resource.

        Returns:
            The newly registered repository file resource.

        Raises:
            ResourceIDReservationNotFoundError: If `resource_id` is provided but
                has no corresponding reservation.
            ResourceAlreadyExistsError: If the destination is already occupied, such as
                by bytes retained after a failed rollback.
            RepositoryResourceFileSystemError: If no file exists at `path`, or the file
                cannot be moved or copied into the repository.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk. Rollback is attempted before this error is propagated.
        """
        path = pathlib.Path(path)
        return self._create_resource(
            factory=lambda destination: RepositoryFile.from_existing_path(
                source_path=path,
                path=destination,
                copy=copy,
                name=name,
                description=description,
                data=data,
            ),
            resource_id=resource_id,
            move_source=path if not copy else None,
        )

    def create_directory(
        self,
        content: bytes | BinaryIO | str | pathlib.Path | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"]
        | None = None,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ) -> RepositoryDirectory:
        """Creates and persists a new directory resource in the repository.

        How `content` is interpreted depends on its type. Raw bytes and open binary
        streams are treated as archive content and unpacked into the new directory using
        `archive_file_format`. A `str` or `pathlib.Path` is instead treated as a path to
        an existing source directory whose tree is copied into the new directory, and
        `archive_file_format` is ignored. Metadata is persisted after creation.
        A failure removes the record, restores an explicit reservation and attempts
        cleanup. Partial placement or failed cleanup can leave unindexed bytes;
        this is not a crash-consistent transaction.

        Args:
            content: Archive content to unpack into the directory (as raw bytes or an
                open binary stream), or a path to an existing source directory to copy
                in, or `None` to create an empty directory.
            archive_file_format: The archive format to use when unpacking `content`.
                Must be set when `content` is archive content. Ignored when `content` is
                a source directory path.
            resource_id: A previously reserved ID to assign to
                this resource. When `None`, a new ID is generated automatically.
            name: A human-readable name for the directory, recorded exactly as given and
                used as the name the resource is served and downloaded under. When
                `None`, the resource UUID is used as the name.
            description: An optional description for the directory.
            data: Optional additional metadata to associate with
                the directory resource.

        Returns:
            The newly created repository directory resource.

        Raises:
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
            ResourceAlreadyExistsError: If the destination is already occupied, such as
                by bytes retained after a failed rollback.
            InvalidRepositoryDirectoryArchiveFileFormatError: If `content` is archive
                content that cannot be unpacked as `archive_file_format`, or if
                `archive_file_format` is not set.
            RepositoryResourceFileSystemError: If the directory cannot be created or the
                source directory or archive cannot be unpacked into it.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk.
        """
        return self._create_resource(
            factory=lambda destination: RepositoryDirectory.create(
                path=destination,
                content=content,
                archive_file_format=archive_file_format,
                name=name if name else destination.name,
                description=description,
                data=data,
            ),
            resource_id=resource_id,
        )

    def add_directory(
        self,
        path: pathlib.Path | str,
        copy: bool = False,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ) -> RepositoryDirectory:
        """Registers an existing directory on disk into the repository.

        Unlike `create_directory`, no new directory content is created: the
        directory at `path` is moved (or copied when `copy=True`) into the
        repository directory under a UUID-based name and registered as a resource.
        When `copy=True`, a new directory is created on disk to hold the copy
        (via `shutil.copytree`) and the original at `path` is left in place; when
        `copy=False` (default), the source directory itself is relocated via
        `shutil.move`, and no copy is made. Metadata is persisted after
        registration. On failure, the record is removed and an explicit reservation
        is restored. Copies are deleted on a best-effort basis; moves are moved back.
        If the source path is occupied or move-back fails, the bytes are retained in
        the repository and both paths are logged. Partial placement, failed cleanup
        and crashes can leave unindexed bytes.

        Args:
            path: Path to the existing directory to register.
            copy: When `False` (default) the source directory is moved into
                the repository. When `True` the source directory is copied and the
                original is left in place.
            resource_id: A previously reserved ID to
                assign to this resource. When `None`, a new ID is generated.
            name: A human-readable name for the directory. When
                `None`, the original directory name is used.
            description: An optional description for the directory.
            data: Optional additional metadata to associate with
                the directory resource.

        Returns:
            The newly registered repository directory resource.

        Raises:
            ResourceIDReservationNotFoundError: If `resource_id` is provided but
                has no corresponding reservation.
            ResourceAlreadyExistsError: If the destination is already occupied, such as
                by bytes retained after a failed rollback.
            RepositoryResourceFileSystemError: If no directory exists at `path`, or the
                directory or any file within it cannot be moved or copied into the
                repository.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk. Rollback is attempted before this error is propagated.
        """
        path = pathlib.Path(path)
        return self._create_resource(
            factory=lambda destination: RepositoryDirectory.from_existing_path(
                source_path=path,
                path=destination,
                copy=copy,
                name=name,
                description=description,
                data=data,
            ),
            resource_id=resource_id,
            move_source=path if not copy else None,
        )

    def update_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        data: dict[str, JsonValue] | None = None,
    ) -> RepositoryFile | RepositoryDirectory:
        """Updates a repository resource's metadata.

        Metadata is persisted after the update. On failure, the previous name,
        description and data are restored on the same live resource object.

        Args:
            resource_id: The ID of the resource to update.
            name: A new human-readable name for the resource, recorded exactly as given
                and used as the name the resource is served and downloaded under. Nothing
                on disk is renamed. When `None`, the existing name is preserved.
            description: A new description for the resource. When `None`, the
                existing description is preserved.
            data: New additional metadata to associate with the resource. When `None`,
                the existing data is preserved.

        Returns:
            The updated repository resource.

        Raises:
            ResourceNotFoundError: If no resource with the given ID exists.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk.
        """
        with self._lock:
            resource_id = normalize_uuid(resource_id)

            resource = self._get_resource_by_resource_id_locked(resource_id)

            previous_fields = resource.name, resource.description, resource.data
            try:
                if name is not None:
                    resource.name = name
                if description is not None:
                    resource.description = description
                if data is not None:
                    resource.data = data
                self._save_repository_metadata_locked()
            except Exception:
                resource.name, resource.description, resource.data = previous_fields
                raise

            return resource

    def delete_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> None:
        """Deletes a repository resource from disk and removes it from the registry.

        Metadata is persisted after deletion. Deleted bytes cannot be rolled back:
        a failed save leaves the resource deregistered in memory and a stale disk
        record that the next load reconciles. A failed directory deletion may leave
        partially deleted contents. This is not a crash-consistent transaction.

        Args:
            resource_id: The ID of the resource to delete.

        A resource whose file or directory is already missing from the repository
        directory is deleted successfully rather than reported as an error. The caller
        asked for the resource not to exist and it does not, so the deregistration below
        is all that is left to do.

        Raises:
            ResourceNotFoundError: If no resource with the given ID exists.
            RepositoryResourceFileSystemError: If the resource cannot be removed from disk.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk.
        """
        with self._lock:
            resource_id = normalize_uuid(resource_id)

            resource = self._get_resource_by_resource_id_locked(resource_id)

            # Missing bytes already satisfy deletion; remove their stale record too.
            try:
                resource.delete()
            except (
                RepositoryFileDoesNotExistError,
                RepositoryDirectoryDoesNotExistError,
            ):
                self._logger.warning(
                    "Deregistered the repository resource '{}' whose {} was already missing "
                    "from the repository directory. The repository metadata was out of sync "
                    "with the contents of the directory on disk.",
                    resource_id,
                    "directory" if resource.is_directory else "file",
                )

            del self._resources[resource_id]

            try:
                self._save_repository_metadata_locked()
            except Exception:
                self._logger.exception(
                    "Resource '{}' was deleted but metadata at '{}' could not be saved; "
                    "the next load will reconcile its missing bytes",
                    resource_id,
                    self._repository_metadata_file_path,
                )
                raise

    def get_all_resources(
        self,
    ) -> list[RepositoryFile | RepositoryDirectory]:
        """Returns all resources currently tracked by the repository service.

        Returns:
            A snapshot list of live repository resources, empty if none exist.
            Their fields and on-disk contents may change concurrently after return.
        """
        with self._lock:
            return list(self._resources.values())

    def get_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        """Returns a repository resource by its ID.

        Args:
            resource_id: The ID of the resource to retrieve.

        Returns:
            The live repository resource. Its fields and on-disk contents may change
            concurrently after return.

        Raises:
            ResourceNotFoundError: If no resource with the given ID exists.
        """
        resource_id = normalize_uuid(resource_id)

        with self._lock:
            return self._get_resource_by_resource_id_locked(resource_id)

    def _get_resource_by_resource_id_locked(
        self, resource_id: str
    ) -> RepositoryFile | RepositoryDirectory:
        try:
            resource = self._resources[resource_id]
        except KeyError:
            raise ResourceNotFoundError(
                resource_id=resource_id,
            ) from None

        return resource
