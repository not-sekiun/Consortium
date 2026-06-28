from pydantic import JsonValue


class BaseFrameworkException(Exception):
    """
    Base exception for all framework related errors.

    Attributes:
        message:
            A human-readable error message.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BaseRaiseOnlyFrameworkException(BaseFrameworkException):
    """
    Base exception for all framework related errors that should only be **raised** from
    within a framework component to explicitly communicate an error condition to the
    calling framework.

    Attributes:
        message:
            A human-readable error message.
        detail:
            Any additional information about the error to be communicated back up to
            the calling framework.
    """

    def __init__(self, message: str, detail: dict[str, JsonValue] | None = None):
        if detail is None:
            detail = {}

        self.message = message
        self.detail = detail

        super().__init__(message)


class BaseCatchOnlyFrameworkException(BaseFrameworkException):
    """
    Base exception for all framework related errors that should only be **caught** from
    within a framework component to explicitly handle an error condition that arose
    from the calling framework.
    """
