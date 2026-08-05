import functools
import json
import os
import pathlib
import uuid
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
    RepositoryMetadataFileUnsyncedError,
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
    format_validation_error,
    normalize_uuid,
    wrap_filesystem_errors,
)

# The metadata file is the only thing this service touches on disk itself. Every operation
# on a resource's own bytes is delegated to the `RepositoryFile` and `RepositoryDirectory`
# objects, which report their own failures as `RepositoryResourceFileSystemError`. That
# keeps the service's filesystem contract to a single question, whether the record of what
# the repository contains could be read or written, and leaves a caller able to tell a
# resource that was never placed from one that was placed but not recorded.
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

        If the metadata file does not yet exist, an empty metadata file is created via
        `save_repository_metadata`. Resources listed in the metadata but missing from
        disk raise an error rather than being silently skipped.

        Raises:
            RepositoryMetadataFileEncodingError: If the metadata file's bytes are
                not valid UTF-8.
            RepositoryMetadataFileJSONError: If the metadata file contains
                invalid JSON.
            RepositoryMetadataFileSchemaError: If the metadata file does not
                follow the expected schema.
            RepositoryMetadataFileUnsyncedError: If a resource recorded in the metadata
                file does not exist on disk.
            RepositoryMetadataFileResourceDataSchemaError: If a `data` field in the
                metadata file fails validation against the repository's `data_model`.
                Only raised when the repository was constructed with a `data_model`.
            RepositoryMetadataFileSystemError: If the metadata file cannot be read from
                disk.
        """
        if not self._repository_metadata_file_path.exists():
            self.save_repository_metadata()
            return

        # The encoding is pinned rather than left to the platform default so that a
        # metadata file written on one machine reads back identically on another. Reading
        # the text and parsing it are separated so that bytes which are not valid UTF-8
        # are reported as a decoding failure rather than surfacing as a JSON syntax error
        # or, worse, decoding cleanly into different characters under a different default.
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

        # `PersistentRepositoryMetadataModel` covers the whole file in one pass: the
        # resource IDs keying it, the shape of every resource entry, and the parsing of
        # the ISO 8601 timestamps into `datetime` objects. Anything malformed surfaces
        # here as a validation error rather than escaping later as a raw `ValueError`
        # while the resources are being reconstructed below.
        try:
            repository_metadata = PersistentRepositoryMetadataModel.model_validate(
                repository_metadata_json,
            ).root
        except ValidationError as exc:
            raise RepositoryMetadataFileSchemaError(
                path=str(self.repository_directory_path),
                validation_error_message=format_validation_error(exc),
            ) from None

        # A resource's `data` is validated separately from the metadata file's own shape
        # so that a failure can be reported against the specific resource carrying the
        # bad data, which a single whole-file validation pass could not attribute.
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

        # Pre-pass check and verify all resources actually exist on disk before
        # populating `self._resources`, so a failure never leaves the registry in a
        # partially-populated state. Checks real filesystem presence rather than
        # trusting the metadata file's own `exists_on_disk` boolean.
        unsynced_resource_ids = []
        resource_id_to_path_and_metadata_map: dict[
            str, tuple[pathlib.Path, PersistentRepositoryResourceModel]
        ] = {}
        for resource_metadata in repository_metadata.values():
            resource_id = str(resource_metadata.resource_id)
            if resource_metadata.is_directory:
                resource_path = self.repository_directory_path / resource_id
            else:
                # A file resource is guaranteed a non-null extension by the metadata
                # model's own validator, so the path reconstruction below is total.
                resource_path = (
                    self.repository_directory_path
                    / f"{resource_id}{resource_metadata.extension}"
                )
            if not resource_path.exists():
                unsynced_resource_ids.append(resource_id)
            else:
                resource_id_to_path_and_metadata_map[resource_id] = (
                    resource_path,
                    resource_metadata,
                )
        if unsynced_resource_ids:
            raise RepositoryMetadataFileUnsyncedError(
                path=str(self.repository_directory_path),
                unsynced_resource_ids=unsynced_resource_ids,
            )

        # After the pre-pass validated all the metadata and computed and validated the
        # actual expected paths to find the resources we load them into the repository
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

            # `resource_id` is generated at instantiation time so we need to override
            # it with the saved `resource_id` which also correlates to the actual path
            # on disk
            resource.resource_id = resource_id
            resource.name = resource_metadata.name
            resource.description = resource_metadata.description
            resource.datetime_created = resource_metadata.datetime_created
            resource.is_directory = resource_metadata.is_directory
            resource.data = resource_metadata.data

            self._resources[resource.resource_id] = resource

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
        repository_metadata_json = {
            resource_id: resource.to_json()
            for resource_id, resource in self._resources.items()
        }
        with _wrap_metadata_filesystem_errors(
            operation="write the repository metadata file",
            path=self._repository_metadata_file_path,
        ):
            # Pinned for the same reason as the read above. There is no encoding error to
            # report on this side: `json.dumps` defaults to `ensure_ascii=True`, so the
            # text handed to the encoder is always pure ASCII and cannot fail to encode.
            with self._repository_metadata_file_path.open(
                mode="w", encoding="utf-8"
            ) as file:
                data = json.dumps(repository_metadata_json, indent=4)
                file.write(data)

    def reserve_resource_id(self) -> uuid.UUID:
        """Generates and reserves a resource ID to be claimed during resource creation.

        The reserved ID must be passed as `resource_id` to `create_file` or
        `create_directory`. This allows the caller to know the resource ID before the
        file or directory is created (e.g., to embed the ID in the file content).

        Returns:
            The reserved resource ID.
        """
        resource_id = uuid.uuid4()
        self._reserved_resource_ids.add(str(resource_id))
        return resource_id

    def create_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ) -> RepositoryFile:
        """Creates and persists a new file resource in the repository.

        The file is stored on disk under a UUID-named path derived from the original
        file extension (if provided). Metadata is persisted after creation.

        Args:
            content: The file content to write.
            name: A human-readable name for the file. When `None`, the
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
            RepositoryResourceFileSystemError: If the file cannot be written to disk.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk.
            UnicodeDecodeError: If `content` is a text stream carrying content that
                cannot be decoded. Left unwrapped as it describes the content the caller
                supplied rather than a failure of the repository itself.
        """
        if resource_id is not None:
            resource_id_str = normalize_uuid(resource_id)
            if resource_id_str not in self._reserved_resource_ids:
                raise ResourceIDReservationNotFoundError(resource_id=resource_id_str)
            self._reserved_resource_ids.discard(resource_id_str)
            unique_resource_id = uuid.UUID(resource_id_str)
        else:
            unique_resource_id = uuid.uuid4()

        # TODO: Implement create_* class methods to allow creating the repository file
        #  in memory and on disk.
        repository_file = RepositoryFile.create(
            # Preserve the original file extension provided from the file name
            # parameter.
            path=self.repository_directory_path
            / f"{unique_resource_id}{os.path.splitext(name)[1] if name else ''}",
            content=content,
            name=name if name else str(unique_resource_id),
            description=description,
            data=data,
        )
        repository_file.resource_id = unique_resource_id
        self._resources[str(repository_file.resource_id)] = repository_file

        self.save_repository_metadata()

        return repository_file

    def add_file(
        self,
        path: pathlib.Path | str,
        copy: bool = False,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        extension: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ) -> RepositoryFile:
        """Registers an existing file on disk into the repository.

        Unlike `create_file`, no new file is written. The file at `path` is moved
        (or copied when `copy=True`) into the repository directory under a
        UUID-based name and registered as a resource. Metadata is persisted after
        registration.

        Args:
            path: Path to the existing file to register.
            copy: When `False` (default) the source file is moved into the
                repository. When `True` the source file is copied and the original
                is left in place.
            resource_id: A previously reserved ID to
                assign to this resource. When `None`, a new ID is generated.
            name: A human-readable display name for the file. Purely
                cosmetic — never affects how the file is stored on disk. When
                `None`, the original filename is used.
            extension: Overrides the file's on-disk extension,
                e.g. `".csv"`. Use this to deliberately reinterpret a file's type
                on ingest. When `None` (default), the source file's own extension
                (`path.suffix`) is used and behavior is unchanged from before.
            description: An optional description for the file.
            data: Optional additional metadata to associate with
                the file resource.

        Returns:
            The newly registered repository file resource.

        Raises:
            ResourceIDReservationNotFoundError: If `resource_id` is provided but
                has no corresponding reservation.
            RepositoryResourceFileSystemError: If no file exists at `path`, or the file
                cannot be moved or copied into the repository.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk. The file has already been moved or copied into the repository by
                this point, so the resource exists on disk without being recorded.
        """
        if isinstance(path, str):
            path = pathlib.Path(path)

        if resource_id is not None:
            resource_id_str = normalize_uuid(resource_id)
            if resource_id_str not in self._reserved_resource_ids:
                raise ResourceIDReservationNotFoundError(resource_id=resource_id_str)
            self._reserved_resource_ids.discard(resource_id_str)
            unique_resource_id = uuid.UUID(resource_id_str)
        else:
            unique_resource_id = uuid.uuid4()

        # `extension=None` means the `RepositoryFile` inherits its `extension` from the
        # source file. An explicit extension is an intentional caller decision to
        # reinterpret the file's type.
        ext = extension if extension is not None else path.suffix
        dest_path = self.repository_directory_path / f"{unique_resource_id}{ext}"

        repository_file = RepositoryFile.from_existing_path(
            source_path=path,
            path=dest_path,
            copy=copy,
            name=name,
            description=description,
            data=data,
        )
        repository_file.resource_id = unique_resource_id
        self._resources[str(repository_file.resource_id)] = repository_file

        self.save_repository_metadata()

        return repository_file

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

        Args:
            content: Archive content to unpack into the directory (as raw bytes or an
                open binary stream), or a path to an existing source directory to copy
                in, or `None` to create an empty directory.
            archive_file_format: The archive format to use when unpacking `content`.
                Must be set when `content` is archive content. Ignored when `content` is
                a source directory path.
            resource_id: A previously reserved ID to assign to
                this resource. When `None`, a new ID is generated automatically.
            name: A human-readable name for the directory. When `None`,
                the resource UUID is used as the name.
            description: An optional description for the directory.
            data: Optional additional metadata to associate with
                the directory resource.

        Returns:
            The newly created repository directory resource.

        Raises:
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
            InvalidRepositoryDirectoryArchiveFileFormatError: If `content` is archive
                content that cannot be unpacked as `archive_file_format`, or if
                `archive_file_format` is not set.
            RepositoryResourceFileSystemError: If the directory cannot be created or the
                source directory or archive cannot be unpacked into it.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk.
        """
        if resource_id is not None:
            resource_id_str = normalize_uuid(resource_id)
            if resource_id_str not in self._reserved_resource_ids:
                raise ResourceIDReservationNotFoundError(resource_id=resource_id_str)
            self._reserved_resource_ids.discard(resource_id_str)
            unique_resource_id = uuid.UUID(resource_id_str)
        else:
            unique_resource_id = uuid.uuid4()

        repository_directory = RepositoryDirectory.create(
            path=self.repository_directory_path / str(unique_resource_id),
            content=content,
            archive_file_format=archive_file_format,
            name=name if name else str(unique_resource_id),
            description=description,
            data=data,
        )
        repository_directory.resource_id = unique_resource_id
        self._resources[str(repository_directory.resource_id)] = repository_directory

        self.save_repository_metadata()

        return repository_directory

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
        registration.

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
            RepositoryResourceFileSystemError: If no directory exists at `path`, or the
                directory or any file within it cannot be moved or copied into the
                repository.
            RepositoryMetadataFileSystemError: If the metadata file cannot be written to
                disk. The directory has already been moved or copied into the repository
                by this point, so the resource exists on disk without being recorded.
        """
        if isinstance(path, str):
            path = pathlib.Path(path)

        if resource_id is not None:
            resource_id_str = normalize_uuid(resource_id)
            if resource_id_str not in self._reserved_resource_ids:
                raise ResourceIDReservationNotFoundError(resource_id=resource_id_str)
            self._reserved_resource_ids.discard(resource_id_str)
            unique_resource_id = uuid.UUID(resource_id_str)
        else:
            unique_resource_id = uuid.uuid4()

        dest_path = self.repository_directory_path / str(unique_resource_id)

        repository_directory = RepositoryDirectory.from_existing_path(
            source_path=path,
            path=dest_path,
            copy=copy,
            name=name,
            description=description,
            data=data,
        )
        repository_directory.resource_id = unique_resource_id
        self._resources[str(repository_directory.resource_id)] = repository_directory

        self.save_repository_metadata()

        return repository_directory

    def update_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        data: dict[str, JsonValue] | None = None,
    ) -> RepositoryFile | RepositoryDirectory:
        """Updates a repository resource's metadata.

        Metadata is persisted after the update.

        Args:
            resource_id: The ID of the resource to update.
            name: A new human-readable name for the resource. When `None`, the
                existing name is preserved.
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
        resource_id = normalize_uuid(resource_id)

        resource = self.get_resource_by_resource_id(
            resource_id=resource_id,
        )

        if name is not None:
            resource.name = name
        if description is not None:
            resource.description = description
        if data is not None:
            resource.data = data

        self.save_repository_metadata()

        return resource

    def delete_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> None:
        """Deletes a repository resource from disk and removes it from the registry.

        Metadata is persisted after deletion.

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
        resource_id = normalize_uuid(resource_id)

        resource = self.get_resource_by_resource_id(
            resource_id=resource_id,
        )

        # Refusing to delete a resource that is already gone from disk would leave its
        # record permanently undeletable, since the deregistration below never runs: the
        # only remaining routes to removing it would be editing the metadata file by hand
        # or recreating the file purely so it can be deleted again. The repository being
        # out of sync is recorded here as a warning instead of being reported to the
        # caller, and `load_repository_metadata` still refuses to load a repository left
        # in that state.
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

        self.save_repository_metadata()

    def get_all_resources(
        self,
    ) -> list[RepositoryFile | RepositoryDirectory]:
        """Returns all resources currently tracked by the repository service.

        Returns:
            A list of all repository resources. Empty if none have been created.
        """
        return list(self._resources.values())

    def get_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        """Returns a repository resource by its ID.

        Args:
            resource_id: The ID of the resource to retrieve.

        Returns:
            The requested repository resource.

        Raises:
            ResourceNotFoundError: If no resource with the given ID exists.
        """
        resource_id = normalize_uuid(resource_id)

        try:
            resource = self._resources[resource_id]
        except KeyError:
            raise ResourceNotFoundError(
                resource_id=resource_id,
            ) from None

        return resource
