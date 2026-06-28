import json
import os
import pathlib
import shutil
import uuid
from datetime import datetime
from typing import BinaryIO, Literal, TextIO

import jsonschema
from loguru import logger

from consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions import (
    InvalidRepositoryMetadataFileJSONError,
    InvalidRepositoryMetadataFileSchemaError,
    RepositoryResourceNotFoundError,
    ResourceIDReservationNotFoundError,
    UnsyncedRepositoryMetadataFileError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class RepositoryService:
    _REPOSITORY_METADATA_JSON_SCHEMA = {
        "type": "object",
        "patternProperties": {
            "^[a-z0-9]+$": {
                "anyOf": [
                    {
                        "type": "object",
                        "properties": {
                            "resource_id": {"type": "string"},
                            "name": {"type": ["string", "null"]},
                            "description": {"type": "string"},
                            "size": {"type": ["integer", "null"]},
                            "exists_on_disk": {"type": "boolean"},
                            "md5_checksum": {"type": ["string", "null"]},
                            "datetime_created": {"type": "string"},
                            "datetime_modified": {"type": "string"},
                            "is_directory": {"type": "boolean"},
                        },
                        "required": [
                            "resource_id",
                            "name",
                            "description",
                            "size",
                            "exists_on_disk",
                            "md5_checksum",
                            "datetime_created",
                            "datetime_modified",
                            "is_directory",
                        ],
                        "additionalProperties": False,
                    },
                    {
                        "type": "object",
                        "properties": {
                            "resource_id": {"type": "string"},
                            "name": {"type": ["string", "null"]},
                            "description": {"type": "string"},
                            "size": {"type": ["integer", "null"]},
                            "exists_on_disk": {"type": "boolean"},
                            "datetime_created": {"type": "string"},
                            "datetime_modified": {"type": "string"},
                            "is_directory": {"type": "boolean"},
                        },
                        "required": [
                            "resource_id",
                            "name",
                            "description",
                            "size",
                            "exists_on_disk",
                            "datetime_created",
                            "datetime_modified",
                            "is_directory",
                        ],
                        "additionalProperties": False,
                    },
                ],
            },
        },
    }

    def __init__(self, repository_directory_path: pathlib.Path):
        self.repository_directory_path = repository_directory_path
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._repository_resources = {}
        self._reserved_resource_ids = set()
        # The repository metadata file is a JSON file that contains the metadata of all
        # the files that are stored on the file system. This is just a JSON dump of the
        # file system metadata that is stored in memory. This allows us to persistently
        # store and reload this information when the server is restarted.
        self._repository_metadata_file_path = (
            repository_directory_path / ".repository.json"
        )

    def __str__(self) -> str:
        return "Repository Service"

    def __repr__(self) -> str:
        return f"RepositoryService(repository_directory_path={self.repository_directory_path!r})"

    @log_and_propagate_error_on_service_method
    def load_repository_metadata(self) -> None:
        """Loads repository resource metadata from the repository metadata JSON file on disk.

        If the metadata file does not yet exist, an empty metadata file is created via
        `save_repository_metadata`. Resources listed in the metadata but missing from
        disk raise an error rather than being silently skipped.

        Returns:
            None

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
        else:
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

            # Pre-pass: verify all resources actually exist on disk before populating
            # self._repository_resources, so a failure never leaves the registry in a
            # partially-populated state. Checks real filesystem presence rather than
            # trusting the metadata file's own exists_on_disk boolean.
            unsynced_resource_ids = []
            for _, repository_resource_json in repository_metadata.items():
                resource_id = repository_resource_json["resource_id"]
                if repository_resource_json["is_directory"]:
                    resource_path = self.repository_directory_path / resource_id
                else:
                    name = repository_resource_json.get("name")
                    ext = os.path.splitext(name)[1] if name else ""
                    resource_path = (
                        self.repository_directory_path / f"{resource_id}{ext}"
                    )
                if not resource_path.exists():
                    unsynced_resource_ids.append(resource_id)
            if unsynced_resource_ids:
                raise UnsyncedRepositoryMetadataFileError(
                    repository_directory_path=str(self.repository_directory_path),
                    unsynced_resource_ids=unsynced_resource_ids,
                )

            # The repository service does some special preprocessing for files or
            # directories that are registered to it. It takes the original path and sets
            # that as the name of the repository file or directory and then renames the
            # new repository file or directory to its file or directory ID. This means
            # that the metadata file that stores the ID also stores its actual path
            # in the repository directory because all repository entities are stored at
            # the root of the repository directory.
            for (
                _,
                repository_resource_json,
            ) in repository_metadata.items():
                if repository_resource_json["is_directory"]:
                    repository_directory = RepositoryDirectory(
                        path=self.repository_directory_path
                        / repository_resource_json["resource_id"],
                    )
                    # Manually reconstruct repository directory from metadata
                    # information.
                    repository_directory.resource_id = repository_resource_json[
                        "resource_id"
                    ]
                    repository_directory.name = repository_resource_json["resource_id"]
                    repository_directory.description = repository_resource_json[
                        "description"
                    ]
                    repository_directory.datetime_created = datetime.fromisoformat(
                        repository_resource_json["datetime_created"],
                    )
                    repository_directory.is_directory = True
                    self._repository_resources[repository_directory.resource_id] = (
                        repository_directory
                    )
                else:
                    # Manually reconstruct repository file from metadata information.
                    repository_file = RepositoryFile(
                        # Take into account the old file extension from the originally
                        # provided file name.
                        path=self.repository_directory_path
                        / f"{repository_resource_json['resource_id']}{os.path.splitext(repository_resource_json['name'])[1] if repository_resource_json['name'] else ''}",
                    )
                    repository_file.resource_id = repository_resource_json[
                        "resource_id"
                    ]
                    repository_file.name = repository_resource_json["name"]
                    repository_file.description = repository_resource_json[
                        "description"
                    ]
                    repository_file.datetime_created = datetime.fromisoformat(
                        repository_resource_json["datetime_created"],
                    )
                    repository_file.is_directory = False
                    self._repository_resources[repository_file.resource_id] = (
                        repository_file
                    )

    @log_and_propagate_error_on_service_method
    def save_repository_metadata(self) -> None:
        """Writes the current in-memory repository resource metadata to disk as JSON.

        Returns:
            None
        """
        repository_metadata_json = {
            resource_id: repository_resource.to_json()
            for resource_id, repository_resource in self._repository_resources.items()
        }
        with self._repository_metadata_file_path.open(mode="w") as file:
            data = json.dumps(repository_metadata_json, indent=4)
            file.write(data)
        self._logger.debug(
            "Saved repository metadata to {} ({} byte(s) written)",
            str(self._repository_metadata_file_path),
            len(data),
        )

    @log_and_propagate_error_on_service_method
    def reserve_resource_id(self) -> uuid.UUID:
        """Generates and reserves a resource ID to be claimed during resource creation.

        The reserved ID must be passed as `resource_id` to `create_file` or
        `create_directory`. This allows the caller to know the resource ID before the
        file or directory is created (e.g., to embed the ID in the file content).

        Returns:
            uuid.UUID: The reserved resource ID.
        """
        resource_id = uuid.uuid4()
        self._reserved_resource_ids.add(str(resource_id))
        self._logger.debug("Reserved resource ID '{}'", str(resource_id))
        return resource_id

    @log_and_propagate_error_on_service_method
    def create_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
    ) -> RepositoryFile:
        """Creates and persists a new file resource in the repository.

        The file is stored on disk under a UUID-named path derived from the original
        file extension (if provided). Metadata is persisted after creation.

        Args:
            content (str | bytes | TextIO | BinaryIO): The file content to write.
            name (str | None): A human-readable name for the file. When `None`, the
                resource UUID is used as the name.
            description (str): An optional description for the file.
            resource_id (str | uuid.UUID | None): A previously reserved ID to assign to
                this resource. When `None`, a new ID is generated automatically.

        Returns:
            RepositoryFile: The newly created repository file resource.

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
        )
        repository_file.resource_id = unique_resource_id
        self._repository_resources[str(repository_file.resource_id)] = repository_file
        self._logger.debug(
            "Created repository file: {!r}",
            repository_file,
        )

        self.save_repository_metadata()

        return repository_file

    @log_and_propagate_error_on_service_method
    def add_file(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
    ) -> RepositoryFile:
        """Registers an existing file on disk into the repository.

        Unlike `create_file`, no new file is written. The file at `path` is moved
        (or copied when `copy=True`) into the repository directory under a
        UUID-based name and registered as a resource. Metadata is persisted after
        registration.

        Args:
            path (pathlib.Path | str): Path to the existing file to register.
            name (str | None): A human-readable name for the file. When `None`,
                the original filename is used.
            description (str): An optional description for the file.
            resource_id (str | uuid.UUID | None): A previously reserved ID to
                assign to this resource. When `None`, a new ID is generated.
            copy (bool): When `False` (default) the source file is moved into the
                repository. When `True` the source file is copied and the original
                is left in place.

        Returns:
            RepositoryFile: The newly registered repository file resource.

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

        dest_path = (
            self.repository_directory_path / f"{unique_resource_id}{path.suffix}"
        )
        if copy:
            shutil.copy2(str(path), dest_path)
        else:
            shutil.move(str(path), dest_path)

        repository_file = RepositoryFile(
            path=dest_path,
            name=name if name else path.name,
            description=description,
        )
        repository_file.resource_id = unique_resource_id
        self._repository_resources[str(repository_file.resource_id)] = repository_file
        self._logger.debug("Added repository file: {!r}", repository_file)

        self.save_repository_metadata()

        return repository_file

    @log_and_propagate_error_on_service_method
    def create_directory(
        self,
        content: bytes | BinaryIO | str | pathlib.Path | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"]
        | None = None,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
    ) -> RepositoryDirectory:
        """Creates and persists a new directory resource in the repository.

        When `content` is provided and `archive_file_format` is set, the content is
        extracted from the archive into the new directory. Metadata is persisted after
        creation.

        Args:
            content (bytes | BinaryIO | str | pathlib.Path | None): Archive content to
                extract into the directory, or `None` to create an empty directory.
            archive_file_format (Literal["zip", "tar", "gztar", "bztar", "xztar"] |
                None): The archive format to use when extracting `content`. Must be set
                when `content` is provided.
            name (str | None): A human-readable name for the directory. When `None`,
                the resource UUID is used as the name.
            description (str): An optional description for the directory.
            resource_id (str | uuid.UUID | None): A previously reserved ID to assign to
                this resource. When `None`, a new ID is generated automatically.

        Returns:
            RepositoryDirectory: The newly created repository directory resource.

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
        )
        repository_directory.resource_id = unique_resource_id
        self._repository_resources[str(repository_directory.resource_id)] = (
            repository_directory
        )
        self._logger.debug(
            "Created repository directory: {!r}",
            repository_directory,
        )

        self.save_repository_metadata()

        return repository_directory

    @log_and_propagate_error_on_service_method
    def add_directory(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
    ) -> RepositoryDirectory:
        """Registers an existing directory on disk into the repository.

        Unlike `create_directory`, no new directory is created. The directory at
        `path` is moved (or copied when `copy=True`) into the repository directory
        under a UUID-based name and registered as a resource. Metadata is persisted
        after registration.

        Args:
            path (pathlib.Path | str): Path to the existing directory to register.
            name (str | None): A human-readable name for the directory. When
                `None`, the original directory name is used.
            description (str): An optional description for the directory.
            resource_id (str | uuid.UUID | None): A previously reserved ID to
                assign to this resource. When `None`, a new ID is generated.
            copy (bool): When `False` (default) the source directory is moved into
                the repository. When `True` the source directory is copied and the
                original is left in place.

        Returns:
            RepositoryDirectory: The newly registered repository directory resource.

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
        )
        repository_directory.resource_id = unique_resource_id
        self._repository_resources[str(repository_directory.resource_id)] = (
            repository_directory
        )
        self._logger.debug("Added repository directory: {!r}", repository_directory)

        self.save_repository_metadata()

        return repository_directory

    @log_and_propagate_error_on_service_method
    def delete_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> None:
        """Deletes a repository resource from disk and removes it from the registry.

        Metadata is persisted after deletion.

        Args:
            resource_id (str | uuid.UUID): The ID of the resource to delete.

        Returns:
            None

        Raises:
            RepositoryResourceNotFoundError: If no resource with the given ID exists.
        """
        repository_resource = self.get_resource_by_resource_id(
            resource_id=resource_id,
        )

        repository_resource.delete()
        del self._repository_resources[resource_id]
        resource_type = "directory" if repository_resource.is_directory else "file"
        self._logger.debug(
            "Deleted repository resource {} {}",
            resource_type,
            str(repository_resource),
        )

        self.save_repository_metadata()

    @log_and_propagate_error_on_service_method
    def get_all_resources(
        self,
    ) -> list[RepositoryFile | RepositoryDirectory]:
        """Returns all resources currently tracked by the repository service.

        Returns:
            list[RepositoryFile | RepositoryDirectory]: A list of all repository
                resources. Empty if none have been created.
        """
        repository_resources = list(self._repository_resources.values())
        self._logger.debug(
            "Retrieved all repository resources ({} resource(s) retrieved)",
            len(repository_resources),
        )
        return repository_resources

    @log_and_propagate_error_on_service_method
    def get_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        """Returns a repository resource by its ID.

        Args:
            resource_id (str | uuid.UUID): The ID of the resource to retrieve.

        Returns:
            RepositoryFile | RepositoryDirectory: The requested repository resource.

        Raises:
            RepositoryResourceNotFoundError: If no resource with the given ID exists.
        """
        resource_id = normalize_uuid(resource_id)

        try:
            repository_resource = self._repository_resources[resource_id]
        except KeyError:
            raise RepositoryResourceNotFoundError(
                resource_id=resource_id,
            ) from None

        self._logger.debug(
            "Retrieved repository resource: {!r}",
            repository_resource,
        )
        return repository_resource
