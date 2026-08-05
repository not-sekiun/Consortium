"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`LoggingServiceError`][consortium.server.exceptions.service_exceptions.logging_service_exceptions.LoggingServiceError]
        - [`SinkNotFoundError`][consortium.server.exceptions.service_exceptions.logging_service_exceptions.SinkNotFoundError]
        - [`SinkLabelAlreadyExistsError`][consortium.server.exceptions.service_exceptions.logging_service_exceptions.SinkLabelAlreadyExistsError]
        - [`SinkConfigurationError`][consortium.server.exceptions.service_exceptions.logging_service_exceptions.SinkConfigurationError]
        - [`SinkFileSystemError`][consortium.server.exceptions.service_exceptions.logging_service_exceptions.SinkFileSystemError]
        - [`StaleSinkHandlerError`][consortium.server.exceptions.service_exceptions.logging_service_exceptions.StaleSinkHandlerError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class LoggingServiceError(BaseServiceError):
    """Base exception for all errors that occur within the logging service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "LOGGING_SERVICE_ERROR"


class SinkNotFoundError(LoggingServiceError):
    """Raised when the requested log sink was not found in the logging service."""

    code = "SINK_NOT_FOUND_ERROR"

    def __init__(self, operation: str, label: str):
        super().__init__(
            message=(
                f"Failed to {operation}. No sink with label '{label}' is "
                f"registered. Check the label against the labels returned by "
                f"`get_all_sinks`."
            ),
            detail={
                "operation": operation,
                "label": label,
            },
        )

    @classmethod
    def _during_removal(cls, label: str) -> SinkNotFoundError:
        return cls(operation="remove the sink", label=label)

    @classmethod
    def _during_modification(cls, label: str) -> SinkNotFoundError:
        return cls(operation="modify the sink", label=label)


class SinkLabelAlreadyExistsError(LoggingServiceError):
    """Raised when attempting to add a log sink with a label that is already in use by
    another registered sink.
    """

    code = "SINK_LABEL_ALREADY_EXISTS_ERROR"

    def __init__(self, label: str):
        super().__init__(
            message=(
                f"Failed to add the sink. A sink with the label '{label}' is "
                f"already registered. Remove the existing sink first, or choose a "
                f"different label."
            ),
            detail={
                "label": label,
            },
        )


class SinkConfigurationError(LoggingServiceError):
    """Raised when loguru's `logger.add` rejects a sink's configuration.

    Wraps the `ValueError` or `TypeError` loguru itself raises when the level, filter,
    or format string is invalid, or when `sink` or one of the forwarded keyword
    arguments is of an unexpected type. This does not cover the sink being an
    unopenable file path, which is reported separately through `SinkFileSystemError`.
    """

    code = "SINK_CONFIGURATION_ERROR"

    def __init__(self, operation: str, label: str, underlying_error: str):
        super().__init__(
            message=(
                f"Failed to {operation}. loguru rejected the configuration for the "
                f"sink labelled '{label}'. {underlying_error}. Check that the level, "
                f"filter, format string, and any other keyword arguments passed to "
                f"the sink are valid."
            ),
            detail={
                "operation": operation,
                "label": label,
                "underlying_error": underlying_error,
            },
        )


class SinkFileSystemError(LoggingServiceError):
    """Raised when a log sink that is a file path cannot be opened by loguru.

    This covers every way the filesystem can refuse to open the sink file: the
    containing directory does not exist, the process lacks the required permissions,
    the configured path points at a directory, the disk is full. They share one type
    because no caller can act differently on any of them: whatever the cause, the sink
    could not be opened, and the specific cause is carried in `message` and `detail`
    for whoever has to fix it.
    """

    code = "SINK_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=f"Failed to {operation} at the path '{path}'. {underlying_error}",
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class StaleSinkHandlerError(LoggingServiceError):
    """Raised when loguru's `logger.remove` rejects a handler ID that this service
    still has registered for a sink.

    This indicates something removed the handler behind this service's back: either
    `logger.remove()` was called directly on loguru, bypassing this service, or a
    second `LoggingService` was constructed, since `LoggingService.__init__` itself
    calls `logger.remove()`, which invalidates every handler ID held by any earlier
    instance.
    """

    code = "STALE_SINK_HANDLER_ERROR"

    def __init__(
        self,
        operation: str,
        label: str,
        handler_id: int,
        underlying_error: str,
    ):
        super().__init__(
            message=(
                f"Failed to {operation}. The handler for the sink '{label}' "
                f"(handler ID {handler_id}) is no longer registered with loguru. "
                f"{underlying_error}. This can happen if `logger.remove()` was "
                f"called directly on loguru, or if a second `LoggingService` was "
                f"constructed and invalidated this instance's handler IDs."
            ),
            detail={
                "operation": operation,
                "label": label,
                "handler_id": handler_id,
                "underlying_error": underlying_error,
            },
        )
