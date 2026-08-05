"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`RepositoryServiceError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryServiceError]
        - [`ResourceNotFoundError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.ResourceNotFoundError]
        - [`ResourceAlreadyExistsError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.ResourceAlreadyExistsError]
        - [`ResourceIDReservationNotFoundError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.ResourceIDReservationNotFoundError]
        - [`RepositoryMetadataFileError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryMetadataFileError]
            - [`RepositoryMetadataFileSystemError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryMetadataFileSystemError]
            - [`RepositoryMetadataFileContentError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryMetadataFileContentError]
                - [`RepositoryMetadataFileEncodingError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryMetadataFileEncodingError]
                - [`RepositoryMetadataFileJSONError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryMetadataFileJSONError]
                - [`RepositoryMetadataFileSchemaError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryMetadataFileSchemaError]
                - [`RepositoryMetadataFileResourceDataSchemaError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryMetadataFileResourceDataSchemaError]
                - [`RepositoryMetadataFileUnsyncedError`][consortium.server.exceptions.service_exceptions.repository_service_exceptions.RepositoryMetadataFileUnsyncedError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class RepositoryServiceError(BaseServiceError):
    """Base exception for all errors that occur within the repository service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "REPOSITORY_SERVICE_ERROR"


class ResourceNotFoundError(RepositoryServiceError):
    """Raised when the requested resource was not found in the repository service."""

    code = "RESOURCE_NOT_FOUND_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to find the requested resource. No resource was found with the "
                f"provided resource ID '{resource_id}'."
            ),
            detail={"resource_id": resource_id},
        )


class ResourceAlreadyExistsError(RepositoryServiceError):
    """Raised when a resource with the provided resource ID already exists in the
    repository service.
    """

    code = "RESOURCE_ALREADY_EXISTS_ERROR"

    def __init__(self, resource_id: str):
        super().__init__(
            message=(
                "Failed to perform the requested operation on the resource. The "
                f"resource with the provided resource ID '{resource_id}' already "
                "exists."
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


class RepositoryMetadataFileError(RepositoryServiceError):
    """Base exception for every failure to get the repository metadata file's data on or
    off disk.

    Catch this to handle "the repository metadata did not make it in or out" without
    caring why. To distinguish a filesystem fault from a bad file, catch
    `RepositoryMetadataFileSystemError` or `RepositoryMetadataFileContentError` instead.
    """

    code = "REPOSITORY_METADATA_FILE_ERROR"


class RepositoryMetadataFileSystemError(RepositoryMetadataFileError):
    """Raised when a filesystem operation on the repository metadata file fails.

    This covers every way the filesystem can refuse the operation: the file does not
    exist, the process lacks the required permissions, the path points at a directory,
    the disk is full. They share one type because no caller can act differently on any of
    them. All of them mean the operation did not happen, and the specific cause is
    carried in `message` and `detail` for whoever has to fix it.

    A file the filesystem hands over successfully but whose contents are wrong is
    reported separately, through `RepositoryMetadataFileContentError`.
    """

    code = "REPOSITORY_METADATA_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=f"Failed to {operation} at the path '{path}'. {underlying_error}",
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class RepositoryMetadataFileContentError(RepositoryMetadataFileError):
    """Base exception for all errors that occur when the repository metadata
    `.repository.json` file's contents are wrong.

    The filesystem handed the file's bytes over successfully, so this is fixed by
    correcting the file rather than by changing the state of the machine or the
    configured path.
    """

    code = "REPOSITORY_METADATA_FILE_CONTENT_ERROR"


class RepositoryMetadataFileEncodingError(RepositoryMetadataFileContentError):
    """Raised when the repository metadata file's bytes cannot be decoded as UTF-8."""

    code = "REPOSITORY_METADATA_FILE_ENCODING_ERROR"

    def __init__(self, path: str, underlying_error: str):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                f"`.repository.json` from the repository directory '{path}'. The "
                f"repository metadata file's bytes could not be decoded as UTF-8. "
                f"{underlying_error}"
            ),
            detail={
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class RepositoryMetadataFileJSONError(RepositoryMetadataFileContentError):
    """Raised when the repository metadata file is not valid JSON during repository
    metadata loading.
    """

    code = "REPOSITORY_METADATA_FILE_JSON_ERROR"

    def __init__(self, path: str):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                f"`.repository.json` from the repository directory '{path}'. The "
                f"repository metadata file is not a valid JSON file."
            ),
            detail={"path": path},
        )


class RepositoryMetadataFileSchemaError(RepositoryMetadataFileContentError):
    """Raised when the repository metadata file does not conform to the expected JSON
    schema during repository metadata loading.
    """

    code = "REPOSITORY_METADATA_FILE_SCHEMA_ERROR"

    def __init__(self, path: str, validation_error_message: str):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                f"`.repository.json` from the repository directory '{path}'. The "
                f"repository metadata file does not conform to the expected JSON "
                f"schema. {validation_error_message}"
            ),
            detail={
                "path": path,
                "validation_error_message": validation_error_message,
            },
        )


class RepositoryMetadataFileResourceDataSchemaError(RepositoryMetadataFileContentError):
    """Raised when the `data` field of a repository resource in the repository metadata
    file does not conform to the expected JSON schema during repository metadata
    loading.
    """

    code = "REPOSITORY_METADATA_FILE_RESOURCE_DATA_SCHEMA_ERROR"

    def __init__(
        self,
        path: str,
        resource_id: str,
        validation_error_message: str,
    ):
        super().__init__(
            message=(
                "Failed to load the repository metadata file "
                f"`.repository.json` from the repository directory '{path}'. The `data` "
                f"field of the repository resource with resource ID '{resource_id}' "
                f"failed validation. {validation_error_message}"
            ),
            detail={
                "path": path,
                "resource_id": resource_id,
                "validation_error_message": validation_error_message,
            },
        )


class RepositoryMetadataFileUnsyncedError(RepositoryMetadataFileContentError):
    """Raised when the repository metadata file is out of sync with the actual contents
    of the repository directory.

    The file parses and validates: what is wrong is that it disagrees with the
    directory. It sits under `RepositoryMetadataFileContentError` because the remedy is
    still to the file's contents rather than to the state of the machine.
    """

    code = "REPOSITORY_METADATA_FILE_UNSYNCED_ERROR"

    def __init__(
        self,
        path: str,
        unsynced_resource_ids: list[str],
    ):
        super().__init__(
            message=(
                "The repository metadata file `.repository.json` in the "
                f"repository directory '{path}' is out of sync with the actual contents "
                f"of the repository. The following resource IDs are recorded in the "
                f"metadata but do not exist on disk: {unsynced_resource_ids}."
            ),
            detail={
                "path": path,
                "unsynced_resource_ids": unsynced_resource_ids,
            },
        )
