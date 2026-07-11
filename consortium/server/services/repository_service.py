import json
import os
import pathlib
import shutil
import uuid
from datetime import datetime
from typing import BinaryIO, Literal, TextIO

import jsonschema
from pydantic import BaseModel, JsonValue, ValidationError

from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    InvalidRepositoryMetadataDataSchemaError,
    InvalidRepositoryMetadataFileJSONError,
    InvalidRepositoryMetadataFileSchemaError,
    RepositoryResourceNotFoundError,
    ResourceIDReservationNotFoundError,
    UnsyncedRepositoryMetadataFileError,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)
from consortium.server.utils import normalize_uuid


class RepositoryService:
    _REPOSITORY_METADATA_JSON_SCHEMA = {
        "type": "object",
        "patternProperties": {
            # Regex to validate UUIDs of any version. Canonically we use UUIDv4 but may
            # consider migrating to v7 in the future
            "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$": {
                "type": "object",
                "properties": {
                    "resource_id": {"type": "string"},
                    "name": {"type": ["string", "null"]},
                    "description": {"type": "string"},
                    "size": {"type": ["integer", "null"]},
                    # Always null for RepositoryDirectories
                    "extension": {"type": ["string", "null"]},
                    "exists_on_disk": {"type": "boolean"},
                    # skip storing the md5 checksum as metadata since it's an
                    # expensive computation and not necessary, checksums are used
                    # client side for download integrity
                    "md5_checksum": {"type": "null"},
                    "datetime_created": {"type": "string"},
                    "datetime_modified": {"type": "string"},
                    "is_directory": {"type": "boolean"},
                    "data": {"type": "object"},
                },
                "required": [
                    "resource_id",
                    "name",
                    "description",
                    "size",
                    "extension",
                    "exists_on_disk",
                    "md5_checksum",
                    "datetime_created",
                    "datetime_modified",
                    "is_directory",
                    "data",
                ],
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    }

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
            InvalidRepositoryMetadataFileJSONError: If the metadata file contains
                invalid JSON.
            InvalidRepositoryMetadataFileSchemaError: If the metadata file does not
                follow the expected schema.
            UnsyncedRepositoryMetadataFileError: If a resource recorded in the metadata
                file does not exist on disk.
        """
        if not self._repository_metadata_file_path.exists():
            self.save_repository_metadata()
            return

        with self._repository_metadata_file_path.open(mode="r") as file:
            try:
                repository_metadata = json.load(file)
                jsonschema.validate(
                    repository_metadata,
                    self._REPOSITORY_METADATA_JSON_SCHEMA,
                )
            except json.JSONDecodeError:
                raise InvalidRepositoryMetadataFileJSONError(
                    repository_directory=str(self.repository_directory_path),
                ) from None
            except jsonschema.ValidationError as exc:
                raise InvalidRepositoryMetadataFileSchemaError(
                    repository_directory=str(self.repository_directory_path),
                    json_schema_error_message=str(exc),
                ) from None

            if self._data_model is not None:
                for resource_id, resource_data in repository_metadata.items():
                    try:
                        self._data_model.model_validate(resource_data["data"])
                    except ValidationError as exc:
                        raise InvalidRepositoryMetadataDataSchemaError(
                            repository_directory=str(self.repository_directory_path),
                            resource_id=resource_id,
                            json_schema_error_message=str(exc),
                        ) from None

        # Pre-pass check and verify all resources actually exist on disk before
        # populating `self._resources`, so a failure never leaves the registry in a
        # partially-populated state. Checks real filesystem presence rather than
        # trusting the metadata file's own `exists_on_disk` boolean.
        unsynced_resource_ids = []
        resource_id_to_path_and_metadata_map: dict[
            str, tuple[pathlib.Path, dict[str, JsonValue]]
        ] = {}
        for resource_json in repository_metadata.values():
            resource_id = resource_json["resource_id"]
            if resource_json["is_directory"]:
                resource_path = self.repository_directory_path / resource_id
            else:
                extension = resource_json["extension"]
                if extension is None:
                    raise InvalidRepositoryMetadataFileSchemaError(
                        repository_directory=str(self.repository_directory_path),
                        json_schema_error_message=(
                            "Repository metadata file contains a file resource with a "
                            "null extension, which is invalid. All file resources must "
                            "have a non-null extension."
                        ),
                    ) from None
                resource_path = (
                    self.repository_directory_path / f"{resource_id}{extension}"
                )
            if not resource_path.exists():
                unsynced_resource_ids.append(resource_id)
            else:
                resource_id_to_path_and_metadata_map[resource_id] = (
                    resource_path,
                    resource_json,
                )
        if unsynced_resource_ids:
            raise UnsyncedRepositoryMetadataFileError(
                repository_directory_path=str(self.repository_directory_path),
                unsynced_resource_ids=unsynced_resource_ids,
            )

        # After the pre-pass validated all the metadata and computed and validated the
        # actual expected paths to find the resources we load them into the repository
        for resource_id, (
            resource_path,
            resource_json,
        ) in resource_id_to_path_and_metadata_map.items():
            if resource_json["is_directory"]:
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
            resource.name = resource_json["name"]
            resource.description = resource_json["description"]
            resource.datetime_created = datetime.fromisoformat(
                resource_json["datetime_created"],
            )
            resource.is_directory = resource_json["is_directory"]
            resource.data = resource_json["data"]

            self._resources[resource.resource_id] = resource

    def save_repository_metadata(self) -> None:
        """Writes the current in-memory repository resource metadata to disk as JSON."""
        repository_metadata_json = {
            resource_id: resource.to_json()
            for resource_id, resource in self._resources.items()
        }
        with self._repository_metadata_file_path.open(mode="w") as file:
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

        if copy:
            shutil.copy2(str(path), dest_path)
        else:
            shutil.move(str(path), dest_path)

        repository_file = RepositoryFile(
            path=dest_path,
            name=name if name else path.name,
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

        When `content` is provided and `archive_file_format` is set, the content is
        extracted from the archive into the new directory. Metadata is persisted after
        creation.

        Args:
            content: Archive content to
                extract into the directory, or `None` to create an empty directory.
            archive_file_format: The archive format to use when extracting `content`.
                Must be set when `content` is provided.
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

        Unlike `create_directory`, no new directory is created. The directory at
        `path` is moved (or copied when `copy=True`) into the repository directory
        under a UUID-based name and registered as a resource. Metadata is persisted
        after registration.

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
        if copy:
            shutil.copytree(str(path), dest_path)
        else:
            shutil.move(str(path), dest_path)

        repository_directory = RepositoryDirectory(
            path=dest_path,
            name=name if name else path.name,
            description=description,
            data=data,
        )
        repository_directory.resource_id = unique_resource_id
        self._resources[str(repository_directory.resource_id)] = repository_directory

        self.save_repository_metadata()

        return repository_directory

    def delete_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> None:
        """Deletes a repository resource from disk and removes it from the registry.

        Metadata is persisted after deletion.

        Args:
            resource_id: The ID of the resource to delete.

        Raises:
            RepositoryResourceNotFoundError: If no resource with the given ID exists.
        """
        resource_id = normalize_uuid(resource_id)

        resource = self.get_resource_by_resource_id(
            resource_id=resource_id,
        )
        resource.delete()
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
            RepositoryResourceNotFoundError: If no resource with the given ID exists.
        """
        resource_id = normalize_uuid(resource_id)

        try:
            resource = self._resources[resource_id]
        except KeyError:
            raise RepositoryResourceNotFoundError(
                resource_id=resource_id,
            ) from None

        return resource
