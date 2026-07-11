"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`RepositoryServiceError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryServiceError]
        - [`RepositoryResourceNotFoundError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryResourceNotFoundError]
        - [`RepositoryResourceAlreadyExistsError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryResourceAlreadyExistsError]
        - [`ResourceIDReservationNotFoundError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.ResourceIDReservationNotFoundError]
        - [`InvalidRepositoryMetadataFileError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.InvalidRepositoryMetadataFileError]
            - [`InvalidRepositoryMetadataFileJSONError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.InvalidRepositoryMetadataFileJSONError]
            - [`InvalidRepositoryMetadataFileSchemaError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.InvalidRepositoryMetadataFileSchemaError]
            - [`UnsyncedRepositoryMetadataFileError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.UnsyncedRepositoryMetadataFileError]
            - [`InvalidRepositoryMetadataDataSchemaError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.InvalidRepositoryMetadataDataSchemaError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class RepositoryServiceError(BaseServiceError):
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
