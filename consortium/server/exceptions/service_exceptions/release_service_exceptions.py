"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`ReleaseServiceError`][consortium.server.exceptions.service_exceptions.release_service_exceptions.ReleaseServiceError]
        - [`ReleaseFileError`][consortium.server.exceptions.service_exceptions.release_service_exceptions.ReleaseFileError]
            - [`ReleaseFileSystemError`][consortium.server.exceptions.service_exceptions.release_service_exceptions.ReleaseFileSystemError]
            - [`ReleaseFileContentError`][consortium.server.exceptions.service_exceptions.release_service_exceptions.ReleaseFileContentError]
                - [`ReleaseFileEncodingError`][consortium.server.exceptions.service_exceptions.release_service_exceptions.ReleaseFileEncodingError]
                - [`ReleaseFileJSONError`][consortium.server.exceptions.service_exceptions.release_service_exceptions.ReleaseFileJSONError]
                - [`ReleaseFileSchemaError`][consortium.server.exceptions.service_exceptions.release_service_exceptions.ReleaseFileSchemaError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class ReleaseServiceError(BaseServiceError):
    """Base exception for all errors that occur within the release service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "RELEASE_SERVICE_ERROR"


class ReleaseFileError(ReleaseServiceError):
    """Base exception for every failure to get the release JSON file's data off disk.

    Catch this to handle "the release information could not be loaded" without caring
    why. To distinguish a filesystem fault from a bad file, catch
    `ReleaseFileSystemError` or `ReleaseFileContentError` instead.
    """

    code = "RELEASE_FILE_ERROR"


class ReleaseFileSystemError(ReleaseFileError):
    """Raised when the release JSON file cannot be read from disk.

    This covers every way the filesystem can refuse the operation: the file does not
    exist, the process lacks the required permissions, the configured path points at a
    directory, the underlying storage fails. They share one type because no caller can
    act differently on any of them: whatever the cause, the release information could
    not be loaded, and the specific cause is carried in `message` and `detail` for
    whoever has to fix it.

    This is a server side fault or misconfiguration: the release JSON file path is fixed
    at server startup and never taken from a client, so a failure here reflects the
    state of the machine the server is running on, the path it was configured with, or a
    bug in the code that supplied that path.

    A file the filesystem hands over successfully but whose contents are wrong is
    reported separately, through `ReleaseFileContentError`.
    """

    code = "RELEASE_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=f"Failed to {operation} at the path '{path}'. {underlying_error}",
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class ReleaseFileContentError(ReleaseFileError):
    """Base exception for all errors that occur when the release JSON file's contents
    are wrong.

    The filesystem handed the file's bytes over successfully, so this is fixed by
    correcting the file rather than by changing the state of the machine or the
    configured path.
    """

    code = "RELEASE_FILE_CONTENT_ERROR"


class ReleaseFileEncodingError(ReleaseFileContentError):
    """Raised when the release JSON file's bytes cannot be decoded as UTF-8."""

    code = "RELEASE_FILE_ENCODING_ERROR"

    def __init__(self, path: str, underlying_error: str):
        super().__init__(
            message=(
                f"Failed to read the release JSON file '{path}'. The file's contents "
                f"are not valid UTF-8 text. {underlying_error}"
            ),
            detail={
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class ReleaseFileJSONError(ReleaseFileContentError):
    """Raised when the release JSON file does not contain valid JSON data."""

    code = "RELEASE_FILE_JSON_ERROR"

    def __init__(self, path: str):
        super().__init__(
            message=(
                f"Failed to process the release JSON file '{path}'. The provided file "
                f"does not contain valid JSON data."
            ),
            detail={"path": path},
        )


class ReleaseFileSchemaError(ReleaseFileContentError):
    """Raised when the release JSON file does not conform to the expected schema."""

    code = "RELEASE_FILE_SCHEMA_ERROR"

    def __init__(self, path: str, validation_error_message: str):
        super().__init__(
            message=(
                f"Failed to process the release JSON file '{path}'. The provided file "
                f"failed validation. {validation_error_message}"
            ),
            detail={
                "path": path,
                "validation_error_message": validation_error_message,
            },
        )
