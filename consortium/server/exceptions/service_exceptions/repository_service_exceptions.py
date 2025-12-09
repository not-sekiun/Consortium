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
                "Failed to find the requested repository resource. No resource was found "
                f"with the provided resource ID '{resource_id}'."
            ),
        )


class RepositoryFileNotFoundError(RepositoryServiceError):
    code = "REPOSITORY_FILE_NOT_FOUND_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to find the requested repository file. No file was found "
                f"with the provided resource ID '{resource_id}'."
            ),
        )


class RepositoryDirectoryNotFoundError(RepositoryServiceError):
    code = "REPOSITORY_DIRECTORY_NOT_FOUND_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to find the requested repository directory. No directory was "
                f"found with the provided resource ID '{resource_id}'."
            ),
        )


class RepositoryResourceAlreadyExistsError(RepositoryServiceError):
    code = "REPOSITORY_RESOURCE_ALREADY_EXISTS_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to perform the requested operation on the repository resource. "
                f"The repository resource with the provided resource ID "
                f"'{resource_id}' already exists."
            ),
        )


class InvalidRepositoryMetadataFile(RepositoryServiceError):
    code = "INVALID_REPOSITORY_METADATA_FILE_ERROR"

    def __init__(self, repository_directory: str, error_message: str = ""):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                "`.repository_metadata.json` from the repository directory "
                f"'{repository_directory}'. {error_message}"
            ),
        )
