import json
import os
import pathlib
import uuid
from datetime import datetime
from typing import BinaryIO, Literal, TextIO

import jsonschema
from loguru import logger

from consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions import (
    InvalidRepositoryMetadataFileJSONError,
    InvalidRepositoryMetadataFileSchemaError,
    RepositoryResourceNotFoundError,
    UnsyncedRepositoryMetadataFileError,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)
from consortium.server.server_logging import LoggerType
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class RepositoryService:
    def __init__(self, repository_directory_path: pathlib.Path):
        self.repository_directory_path = repository_directory_path
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._repository_resources = {}
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
        repository_metadata_json_schema = {
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
        if not self._repository_metadata_file_path.exists():
            self.save_repository_metadata()
        else:
            with self._repository_metadata_file_path.open(mode="r") as file:
                try:
                    repository_metadata = json.load(file)
                    jsonschema.validate(
                        repository_metadata,
                        repository_metadata_json_schema,
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

                # TODO: Handle conditions where the metadata corrupts and no longer
                #  corresponds to the actual state of affairs in the repository directory
                if not repository_resource_json["exists_on_disk"]:
                    raise UnsyncedRepositoryMetadataFileError(
                        repository_directory_path=str(self.repository_directory_path)
                    )

    @log_and_propagate_error_on_service_method
    def save_repository_metadata(self) -> None:
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
    def create_repository_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        binary: bool = True,
        name: str | None = None,
        description: str = "",
    ) -> RepositoryFile:
        # TODO: Fix this hack. We should add a class method that allows manually
        #  setting each particular relevant value for "loading" back in a previously
        #  tracked file.
        unique_resource_id = uuid.uuid4()
        # TODO: Implement create_* class methods to allow creating the repository file
        #  in memory and on disk.
        repository_file = RepositoryFile.create(
            # Preserve the original file extension provided from the file name
            # parameter.
            path=self.repository_directory_path
            / f"{unique_resource_id}{os.path.splitext(name)[1] if name else ''}",
            content=content,
            binary=binary,
            name=name if name else unique_resource_id,
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
    def create_repository_directory(
        self,
        content: bytes | BinaryIO | str | pathlib.Path,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"],
        name: str | None = None,
        description: str = "",
    ) -> RepositoryDirectory:
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
    def delete_repository_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> None:
        repository_resource = self.get_repository_resource_by_resource_id(
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
    def get_all_repository_resources(
        self,
    ) -> list[RepositoryFile | RepositoryDirectory]:
        repository_resources = list(self._repository_resources.values())
        self._logger.debug(
            "Retrieved all repository resources ({} resource(s) retrieved)",
            len(repository_resources),
        )
        return repository_resources

    @log_and_propagate_error_on_service_method
    def get_repository_resource_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
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
