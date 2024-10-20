import json
import os
import pathlib
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import IO, BinaryIO, Literal

import jsonschema
from loguru import logger

from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    InvalidRepositoryMetadataFile,
    RepositoryDirectoryNotFoundError,
    RepositoryFileNotFoundError,
    RepositoryResourceAlreadyExistsError,
    RepositoryResourceNotFoundError,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)


# TODO: Create an optimization that can detect duplicate file uploads and map several
#  identical UUIDs to the same file.
# TODO: Migrate to aiofiles
class RepositoryService:
    def __init__(self, repository_directory_path: pathlib.Path):
        self._repository_directory_path = repository_directory_path
        self.repository_service_logger = logger.bind(
            logger_name=str(self),
        )
        self._repository_resources = {}
        # The repository metadata file is a JSON file that contains the metadata of all
        # the files that are stored on the file system. This is just a JSON dump of the
        # file system metadata that is stored in memory. This allows us to persistently
        # store and reload this information when the server is restarted.
        self._repository_metadata_file_path = (
            repository_directory_path / ".repository_metadata.json"
        )
        self.load_repository_metadata()

    def __str__(self) -> str:
        return "Repository Service"

    def __repr__(self) -> str:
        return f"RepositoryService(repository_directory_path={self._repository_directory_path!r})"

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
                                "datetime_updated": {"type": "string"},
                                "is_directory": {"type": "boolean"},
                            },
                            "required": [
                                "resource_id" "name",
                                "description",
                                "size",
                                "exists_on_disk",
                                "md5_checksum",
                                "datetime_created",
                                "datetime_updated",
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
                                "datetime_updated": {"type": "string"},
                                "is_directory": {"type": "boolean"},
                            },
                            "required": [
                                "resource_id",
                                "name",
                                "description",
                                "size",
                                "exists_on_disk",
                                "datetime_created",
                                "datetime_updated",
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
                    raise InvalidRepositoryMetadataFile(
                        error_message=(
                            "The repository metadata file does not contain valid "
                            "JSON data."
                        ),
                        repository_directory=str(self._repository_directory_path),
                    )
                except jsonschema.ValidationError as exc:
                    raise InvalidRepositoryMetadataFile(
                        error_message=(
                            "The repository metadata file does not contain valid "
                            f"JSON that conforms to the expected JSON schema. {exc}"
                        ),
                        repository_directory=str(self._repository_directory_path),
                    )

            # The repository service does some special preprocessing for files or
            # directories that are registered to it. It takes the original path and sets
            # that as the name of the repository file or directory and then renames the
            # new repository file or directory to its file or directory ID. This means
            # that the metadata file that stores the ID also stores its actual path
            # in the repository directory because all repository entities are stored at
            # the root of the repository directory.
            for (
                resource_id,
                repository_resource_json,
            ) in repository_metadata.items():
                if repository_resource_json["is_directory"]:
                    repository_directory = RepositoryDirectory(
                        path=self._repository_directory_path
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
                    repository_directory.datetime_updated = datetime.fromisoformat(
                        repository_resource_json["datetime_updated"],
                    )
                    repository_directory.is_directory = True
                    self.register_repository_resource(
                        repository_resource=repository_directory,
                    )
                else:
                    # Manually reconstruct repository file from metadata information.
                    repository_file = RepositoryFile(
                        # Take into account the old file extension from the originally
                        # provided file name.
                        path=self._repository_directory_path
                        / f"{repository_resource_json["resource_id"]}{os.path.splitext(repository_resource_json["name"])[1] if repository_resource_json["name"] else ""}",
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
                    repository_file.datetime_updated = datetime.fromisoformat(
                        repository_resource_json["datetime_updated"],
                    )
                    repository_file.is_directory = False
                    self.register_repository_resource(
                        repository_resource=repository_file,
                    )

                # TODO: Handle conditions where the metadata corrupts and no longer
                #  corresponds to the actual state of affairs in the repository directory
                if not repository_resource_json["exists_on_disk"]:
                    raise InvalidRepositoryMetadataFile(
                        error_message=(
                            "The repository metadata file contains repository entities "
                            "that do not have any corresponding entities on disk."
                        ),
                        repository_directory=str(self._repository_directory_path),
                    )

    def save_repository_metadata(self) -> None:
        repository_metadata_json = {
            resource_id: repository_resource.to_json()
            for resource_id, repository_resource in self._repository_resources.items()
        }
        with self._repository_metadata_file_path.open(mode="w") as file:
            json.dump(repository_metadata_json, file)

    def register_repository_resource(
        self,
        repository_resource: RepositoryFile | RepositoryDirectory,
    ) -> None:
        if str(repository_resource.resource_id) in self._repository_resources:
            raise RepositoryResourceAlreadyExistsError(
                resource_id=str(repository_resource.resource_id),
            )

        self._repository_resources[str(repository_resource.resource_id)] = (
            repository_resource
        )
        self.save_repository_metadata()

        repository_resource_type = (
            "directory" if repository_resource.is_directory else "file"
        )
        self.repository_service_logger.debug(
            "Registered repository {} {}",
            repository_resource_type,
            str(repository_resource),
        )

    def deregister_repository_resource_by_resource_id(
        self,
        resource_id: str,
    ) -> None:
        try:
            deregistered_repository_resource = self._repository_resources.pop(
                resource_id,
            )
        except KeyError:
            raise RepositoryResourceNotFoundError(
                resource_id=resource_id,
            )

        repository_resource_type = (
            "directory" if deregistered_repository_resource.is_directory else "file"
        )
        self.repository_service_logger.debug(
            "Deregistered repository {} {}",
            repository_resource_type,
            str(deregistered_repository_resource),
        )

    def create_repository_file(
        self,
        data: str
        | bytes
        | IO
        | Generator[bytes, None, None]
        | Generator[str, None, None],
        is_binary: bool = True,
        name: str | None = None,
        description: str = "",
    ) -> RepositoryFile:
        # TODO: Fix this hack. We should add a class method that allows manually
        #  setting each particular relevant value for "loading" back in a previously
        #  tracked file.
        unique_resource_id = uuid.uuid4()
        # TODO: Implement create_* class methods to allow creating the repository file
        #  in memory and on disk.
        repository_file = RepositoryFile.create_new_file_on_disk(
            # Preserve the original file extension provided from the file name
            # parameter.
            path=self._repository_directory_path
            / f"{unique_resource_id}{os.path.splitext(name)[1] if name else ""}",
            name=name if name else unique_resource_id,
            description=description,
        )
        repository_file.resource_id = unique_resource_id

        if isinstance(data, bytes):
            repository_file.write(data, write_file_as_binary=is_binary)
        elif isinstance(data, Generator):
            repository_file.write_from_generator(data, write_file_as_binary=is_binary)
        elif isinstance(data, IO):
            repository_file.write_from_file_object(data, write_file_as_binary=is_binary)
        else:
            # TODO: Consider maybe raising an error instead of just trying to force a
            #  write
            repository_file.write(data, write_file_as_binary=is_binary)

        self.register_repository_resource(repository_resource=repository_file)
        self.save_repository_metadata()

        return repository_file

    def delete_repository_file_by_resource_id(self, resource_id: str) -> None:
        repository_resource = self.get_repository_resource_by_resource_id(
            resource_id=resource_id,
        )
        repository_resource.delete()
        self.deregister_repository_resource_by_resource_id(
            resource_id=resource_id,
        )
        self.save_repository_metadata()

    def create_repository_directory(
        self,
        archive_file: bytes | Generator[bytes, None, None] | BinaryIO,
        format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> RepositoryDirectory:
        unique_resource_id = uuid.uuid4()

        if isinstance(archive_file, bytes):
            repository_directory = (
                RepositoryDirectory.create_on_disk_from_archive_file_data(
                    path=self._repository_directory_path / str(unique_resource_id),
                    archive_file_data=archive_file,
                    format=format,
                    name=name if name else str(unique_resource_id),
                    description=description,
                )
            )
            repository_directory.resource_id = unique_resource_id
        elif isinstance(archive_file, Generator):
            repository_directory = (
                RepositoryDirectory.create_on_disk_from_archive_file_data_generator(
                    path=self._repository_directory_path / str(unique_resource_id),
                    archive_file_data_generator=archive_file,
                    format=format,
                    name=name if name else str(unique_resource_id),
                    description=description,
                )
            )
            repository_directory.resource_id = unique_resource_id
        elif isinstance(archive_file, BinaryIO):
            repository_directory = (
                RepositoryDirectory.create_on_disk_from_archive_file_data_file_object(
                    path=self._repository_directory_path / str(unique_resource_id),
                    archive_file_data_file_object=archive_file,
                    format=format,
                    name=name if name else str(unique_resource_id),
                    description=description,
                )
            )
            repository_directory.resource_id = unique_resource_id
        else:
            # TODO: Consider maybe raising an error instead of just trying to force a
            #  write
            repository_directory = (
                RepositoryDirectory.create_on_disk_from_archive_file_data(
                    path=self._repository_directory_path / str(unique_resource_id),
                    name=name if name else str(unique_resource_id),
                    description=description,
                    archive_file_data=archive_file,
                )
            )
            repository_directory.resource_id = unique_resource_id

        self.register_repository_resource(repository_resource=repository_directory)
        self.save_repository_metadata()

        return repository_directory

    def delete_repository_directory_by_resource_id(self, resource_id: str) -> None:
        repository_resource = self.get_repository_resource_by_resource_id(
            resource_id=resource_id,
        )
        repository_resource.delete(recursive=True)
        self.deregister_repository_resource_by_resource_id(
            resource_id=resource_id,
        )
        self.save_repository_metadata()

    def delete_repository_resource_by_resource_id(
        self,
        resource_id: str,
    ) -> None:
        repository_resource = self.get_repository_resource_by_resource_id(
            resource_id=resource_id,
        )
        if isinstance(repository_resource, RepositoryFile):
            repository_resource.delete()
        else:
            repository_resource.delete(recursive=True)
        self.deregister_repository_resource_by_resource_id(
            resource_id=resource_id,
        )
        self.save_repository_metadata()

    def get_all_repository_resources(
        self,
    ) -> list[RepositoryFile | RepositoryDirectory]:
        return list(self._repository_resources.values())

    def get_all_repository_files(self) -> list[RepositoryFile]:
        return [
            file
            for file in self._repository_resources.values()
            if isinstance(file, RepositoryFile)
        ]

    def get_all_repository_directories(self) -> list[RepositoryDirectory]:
        return [
            directory
            for directory in self._repository_resources.values()
            if isinstance(directory, RepositoryDirectory)
        ]

    def get_repository_resource_by_resource_id(
        self,
        resource_id: str,
    ) -> RepositoryFile | RepositoryDirectory:
        try:
            return self._repository_resources[resource_id]
        except KeyError:
            raise RepositoryResourceNotFoundError(
                resource_id=resource_id,
            )

    def get_repository_file_by_resource_id(self, resource_id: str) -> RepositoryFile:
        file_system_resource = self.get_repository_resource_by_resource_id(
            resource_id=resource_id,
        )
        if isinstance(file_system_resource, RepositoryFile):
            return file_system_resource
        raise RepositoryFileNotFoundError(resource_id=resource_id)

    def get_repository_directory_by_resource_id(
        self,
        resource_id: str,
    ) -> RepositoryDirectory:
        file_system_resource = self.get_repository_resource_by_resource_id(
            resource_id=resource_id,
        )
        if isinstance(file_system_resource, RepositoryDirectory):
            return file_system_resource
        raise RepositoryDirectoryNotFoundError(resource_id=resource_id)
