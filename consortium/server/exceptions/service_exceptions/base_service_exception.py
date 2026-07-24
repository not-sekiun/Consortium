"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
"""

from typing import ClassVar

from pydantic import JsonValue


class BaseServiceError(Exception):
    """Base exception for all errors raised by the server's services.

    Every service level exception derives from this class so that service errors can be
    caught and handled through a single common type.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional JSON-serializable, structured, machine-readable context about
            the error, or None when there is no such context.
    """

    code: ClassVar[str] = "BASE_SERVICE_ERROR"

    def __init__(self, message: str = "", detail: dict[str, JsonValue] | None = None):
        self.message: str = message
        self.detail: dict[str, JsonValue] | None = detail
        super().__init__(message)
