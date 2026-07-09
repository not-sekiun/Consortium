"""Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`RepositoryError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryError]
        - [`RepositoryServiceError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryServiceError]
            - [`RepositoryResourceNotFoundError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryResourceNotFoundError]
            - [`RepositoryResourceAlreadyExistsError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryResourceAlreadyExistsError]
            - [`ResourceIDReservationNotFoundError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.ResourceIDReservationNotFoundError]
            - [`InvalidRepositoryMetadataFileError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.InvalidRepositoryMetadataFileError]
                - [`InvalidRepositoryMetadataFileJSONError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.InvalidRepositoryMetadataFileJSONError]
                - [`InvalidRepositoryMetadataFileSchemaError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.InvalidRepositoryMetadataFileSchemaError]
                - [`UnsyncedRepositoryMetadataFileError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.UnsyncedRepositoryMetadataFileError]
                - [`InvalidRepositoryMetadataDataSchemaError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.InvalidRepositoryMetadataDataSchemaError]
        - [`RepositoryFrameworkError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryFrameworkError]
            - [`RepositoryFileError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryFileError]
                - [`RepositoryFileAlreadyExistsError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryFileAlreadyExistsError]
                - [`RepositoryFileDoesNotExistError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryFileDoesNotExistError]
            - [`RepositoryDirectoryError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryDirectoryError]
                - [`RepositoryDirectoryAlreadyExistsError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryDirectoryAlreadyExistsError]
                - [`RepositoryDirectoryDoesNotExistError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryDirectoryDoesNotExistError]
                - [`RelativePathOutsideRepositoryDirectoryError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RelativePathOutsideRepositoryDirectoryError]
                - [`RepositoryDirectoryRelativePathNotContainedError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.RepositoryDirectoryRelativePathNotContainedError]
                - [`InvalidRepositoryDirectoryArchiveFileFormatError`][consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions.InvalidRepositoryDirectoryArchiveFileFormatError]
"""

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class RepositoryError(BaseConsortiumError):
    """Base exception for all repository-related errors."""

    code = "REPOSITORY_ERROR"


class RepositoryServiceError(RepositoryError):
    """Base exception for all errors that occur within the repository service."""

    code = "REPOSITORY_SERVICE_ERROR"


class RepositoryResourceNotFoundError(RepositoryServiceError):
    """Raised when the requested repository resource was not found in the repository
    service.
    """

    code = "REPOSITORY_RESOURCE_NOT_FOUND_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to find the requested repository resource. No resource "
                f"was found with the provided resource ID '{resource_id}'."
            ),
            detail={"resource_id": resource_id},
        )


class RepositoryResourceAlreadyExistsError(RepositoryServiceError):
    """Raised when a repository resource with the provided resource ID already exists in
    the repository service.
    """

    code = "REPOSITORY_RESOURCE_ALREADY_EXISTS_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to perform the requested operation on the repository resource. "
                f"The repository resource with the provided resource ID '{resource_id}' "
                "already exists."
            ),
            detail={"resource_id": resource_id},
        )


class ResourceIDReservationNotFoundError(RepositoryServiceError):
    """Raised when a resource ID passed to create_file or create_directory has no
    matching reservation.
    """

    code = "RESOURCE_ID_RESERVATION_NOT_FOUND_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                f"Failed to create the repository resource and assign it the provided "
                f"resource ID. No reservation was found for the provided resource ID "
                f"'{resource_id}'. Reserve a resource ID first using "
                f"`RepositoryService.reserve_resource_id` before creating a resource "
                f"with that ID."
            ),
            detail={"resource_id": resource_id},
        )


class InvalidRepositoryMetadataFileError(RepositoryServiceError):
    """Base exception for all errors that occur due to an invalid repository metadata
    `.repository.json` file.
    """

    code = "INVALID_REPOSITORY_METADATA_FILE_ERROR"


class InvalidRepositoryMetadataFileJSONError(
    InvalidRepositoryMetadataFileError,
):
    """Raised when the repository metadata file is not valid JSON during repository
    metadata loading.
    """

    code = "INVALID_REPOSITORY_METADATA_FILE_JSON_ERROR"

    def __init__(self, repository_directory: str):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                "`.repository.json` from the repository directory "
                f"'{repository_directory}'. The repository metadata file is not "
                f"a valid JSON file."
            ),
            detail={"repository_directory": repository_directory},
        )


class InvalidRepositoryMetadataFileSchemaError(
    InvalidRepositoryMetadataFileError,
):
    """Raised when the repository metadata file does not conform to the expected JSON
    schema during repository metadata loading.
    """

    code = "INVALID_REPOSITORY_METADATA_FILE_SCHEMA_ERROR"

    def __init__(self, repository_directory: str, json_schema_error_message: str):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                "`.repository.json` from the repository directory "
                f"'{repository_directory}'. The repository metadata file does not "
                f"conform to the expected JSON schema. {json_schema_error_message}"
            ),
            detail={
                "repository_directory": repository_directory,
                "json_schema_error_message": json_schema_error_message,
            },
        )


class UnsyncedRepositoryMetadataFileError(InvalidRepositoryMetadataFileError):
    """Raised when the repository metadata file is out of sync with the actual contents
    of the repository directory.
    """

    code = "UNSYNCED_REPOSITORY_METADATA_FILE_ERROR"

    def __init__(
        self,
        repository_directory_path: str,
        unsynced_resource_ids: list[str],
    ):
        super().__init__(
            message=(
                "The repository metadata file `.repository.json` in the "
                f"repository directory '{repository_directory_path}' is out of sync "
                f"with the actual contents of the repository. The following resource "
                f"IDs are recorded in the metadata but do not exist on disk: "
                f"{unsynced_resource_ids}."
            ),
            detail={
                "repository_directory_path": repository_directory_path,
                "unsynced_resource_ids": unsynced_resource_ids,
            },
        )


class InvalidRepositoryMetadataDataSchemaError(InvalidRepositoryMetadataFileError):
    """Raised when the `data` field of a repository resource in the repository metadata
    file does not conform to the expected JSON schema during repository metadata
    loading.
    """

    code = "INVALID_REPOSITORY_METADATA_DATA_SCHEMA_ERROR"

    def __init__(
        self,
        repository_directory: str,
        resource_id: str,
        json_schema_error_message: str,
    ):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                "`.repository.json` from the repository directory "
                f"'{repository_directory}'. The `data` field of the repository resource "
                f"with resource ID '{resource_id}' does not conform to the expected "
                f"JSON schema. {json_schema_error_message}"
            ),
            detail={
                "repository_directory": repository_directory,
                "resource_id": resource_id,
                "json_schema_error_message": json_schema_error_message,
            },
        )


class RepositoryFrameworkError(RepositoryError):
    """Base exception for all errors that occur within the repository framework."""

    code = "REPOSITORY_FRAMEWORK_ERROR"


class RepositoryFileError(RepositoryFrameworkError):
    """Base exception for all errors that occur when performing operations on a repository
    file.
    """

    code = "REPOSITORY_FILE_ERROR"


class RepositoryFileAlreadyExistsError(RepositoryFileError):
    """Raised when attempting to perform an operation on a repository file that requires
    the file to not exist but the file already exists on disk.
    """

    code = "REPOSITORY_FILE_ALREADY_EXISTS_ERROR"

    def __init__(self, repository_file_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the file {repository_file_str}. The "
            f"file already exists on the disk.",
        )


class RepositoryFileDoesNotExistError(RepositoryFileError):
    """Raised when attempting to perform an operation on a repository file that requires
    the file to exist but the file does not exist on disk.
    """

    code = "REPOSITORY_FILE_DOES_NOT_EXIST_ERROR"

    def __init__(self, repository_file_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the file {repository_file_str}. The "
            f"file does not exist on the disk.",
        )


class RepositoryDirectoryError(RepositoryFrameworkError):
    """Base exception for all errors that occur when performing operations on a repository
    directory.
    """

    code = "REPOSITORY_DIRECTORY_ERROR"


class RepositoryDirectoryAlreadyExistsError(RepositoryDirectoryError):
    """Raised when attempting to perform an operation on a repository directory that
    requires the directory to not exist but the directory already exists on disk.
    """

    code = "REPOSITORY_DIRECTORY_ALREADY_EXISTS_ERROR"

    def __init__(self, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"{repository_directory_str}. The directory already exists on the disk.",
        )


class RepositoryDirectoryDoesNotExistError(RepositoryDirectoryError):
    """Raised when attempting to perform an operation on a repository directory that
    requires the directory to exist but the directory does not exist on disk.
    """

    code = "REPOSITORY_DIRECTORY_DOES_NOT_EXIST_ERROR"

    def __init__(self, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"{repository_directory_str}. The directory does not exist on the disk.",
        )


class RelativePathOutsideRepositoryDirectoryError(RepositoryDirectoryError):
    """Raised when a relative path provided to a repository directory operation resolves
    to a location outside of the repository directory.
    """

    code = "RELATIVE_PATH_OUTSIDE_REPOSITORY_DIRECTORY_ERROR"

    def __init__(self, relative_path: str, repository_directory_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the path '{relative_path}' "
            f"relative to the directory {repository_directory_str}. The path is outside "
            f"of the repository directory.",
        )


class RepositoryDirectoryRelativePathNotContainedError(RepositoryDirectoryError):
    """Raised when a relative path provided to a repository directory operation resolves
    to a location that is not contained within the repository directory.
    """

    code = "REPOSITORY_DIRECTORY_RELATIVE_PATH_NOT_CONTAINED_ERROR"

    def __init__(self, relative_path: str, repository_directory_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the path '{relative_path}' "
            f"relative to the directory {repository_directory_str}. The path provided "
            f"when resolved is not contained within the repository directory.",
        )


class InvalidRepositoryDirectoryArchiveFileFormatError(RepositoryDirectoryError):
    """Raised when an unsupported archive file format is provided when attempting to
    create a repository directory from an archive file.
    """

    code = "INVALID_REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_ERROR"

    def __init__(self, archive_file_format: str) -> None:
        super().__init__(
            f"Failed to create a repository directory from the provided archive file. "
            f"The archive file format '{archive_file_format}' is not supported.",
        )
