from typing import Any


class BaseFrameworkException(Exception):
    """
    Base exception for all framework related errors. This exception is meant to be used
    to catch and handle all errors that are raised from framework objects across the
    application.

    Exceptions of this class are distinctly different from the "signalling" exceptions
    that are present in the [`consortium.framework.exceptions`][consortium.framework.exceptions]
    module. The exceptions here do not serve any message passing purpose to or from the
    framework objects. Instead, they are raised when an error condition occurs.

    Attributes:
        code: A **stable, machine-readable identifier** for the specific type of
            service error.
        message: A human-readable message that describes the error condition that
            occurred.
        detail: Any JSON-serializable data structure holding **structured, raw data**
            relevant to the failure.
    """

    code: str

    def __init__(self, message: str, detail: Any = None):
        self.message = message
        self.detail = detail
        super().__init__(message)

    def to_json(self) -> dict[str, Any]:
        """
        Convert the exception to a JSON-serializable dictionary.

        Returns:
            A dictionary that contains the code, message, and detail of the exception.
        """
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }
