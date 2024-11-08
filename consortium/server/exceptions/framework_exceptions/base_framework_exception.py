from typing import Any


class BaseFrameworkException(Exception):
    """
    Base exception for all framework related errors. This exception is meant to be used
    throughout the REST API layer to catch and handle all framework related errors.
    Exceptions of this class are distinctly different from the "signalling" exceptions
    that are present in the [`consortium.framework.exceptions`][consortium.framework.exceptions]
    module. The exceptions here do not serve any message passing or signalling purpose to or
    from the framework. Instead, they are raised when an error condition occurs.

    Attributes:
        message (str): A human-readable message that describes the error condition that
            occurred.
        detail (Any): Additional details about the error condition that occurred. This
            can be any type of JSON-serializable data structure that provides more
            context about the error.
    """

    def __init__(self, message: str, detail: Any = None):
        self.message = message
        """
        A human-readable message that describes the error condition that occurred.
        """
        self.detail = detail
        """
        Additional details about the error condition that occurred. This can be any
        type of JSON-serializable data structure that provides more context about the
        error.
        """
        super().__init__(message)

    def to_json(self) -> dict[str, Any]:
        """
        Convert the exception to a JSON-serializable dictionary.

        Returns:
            A dictionary that contains the message and detail of the exception.
        """
        return {
            "message": self.message,
            "detail": self.detail,
        }
