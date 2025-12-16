from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class RepositoryServiceError(BaseServiceException):
    code = "REPOSITORY_SERVICE_ERROR"


class RepositoryResourceNotFoundError(RepositoryServiceError):
    code = "REPOSITORY_RESOURCE_NOT_FOUND_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to find the requested repository resource. No resource "
                f"was found with the provided resource ID '{resource_id}'."
            ),
            detail={"resource_id": resource_id},
        )


class RepositoryFileNotFoundError(RepositoryServiceError):
    code = "REPOSITORY_RESOURCE_FILE_NOT_FOUND_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to find the requested repository file. No file was found with the "
                f"provided resource ID '{resource_id}'."
            ),
            detail={"resource_id": resource_id},
        )


class RepositoryDirectoryNotFoundError(RepositoryServiceError):
    code = "REPOSITORY_DIRECTORY_NOT_FOUND_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to find the requested repository directory. No directory was "
                f"found with the provided resource ID '{resource_id}'."
            ),
            detail={"resource_id": resource_id},
        )


class RepositoryResourceAlreadyExistsError(RepositoryServiceError):
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


class InvalidRepositoryMetadataFileError(RepositoryServiceError):
    code = "INVALID_REPOSITORY_METADATA_FILE_ERROR"


class InvalidRepositoryMetadataFileJSONError(
    InvalidRepositoryMetadataFileError,
):
    code = "INVALID_REPOSITORY_METADATA_FILE_JSON_ERROR"

    def __init__(self, repository_directory: str):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                "`.repository.json` from the repository directory "
                f"'{repository_directory}'. The repository metadata file is not"
                f"a valid JSON file. "
            ),
            detail={"repository_directory": repository_directory},
        )


class InvalidRepositoryMetadataFileSchemaError(
    InvalidRepositoryMetadataFileError,
):
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
    code = "UNSYNCED_REPOSITORY_METADATA_FILE_ERROR"

    def __init__(self, repository_directory_path: str):
        super().__init__(
            message=(
                "The repository metadata file `.repository.json` in the "
                f"repository directory '{repository_directory_path}' is out of sync "
                f"with the actual contents of the repository."
            ),
            detail={"repository_directory_path": repository_directory_path},
        )
