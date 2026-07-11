from pydantic import JsonValue


class BaseFrameworkError(Exception):
    """Base exception for all errors raised by the framework primitives.

    Every framework level exception derives from this class so that framework errors can
    be caught, translated into API exceptions, and logged through a single common type.

    Attributes:
        code: A stable machine-readable string identifying the specific error. It lets
            the API layer correlate the exception with a matching API exception and
            HTTP status code without relying on the exception's class.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured, machine-readable context about the error, or None
            when there is no such context.
    """

    code: str = "BASE_FRAMEWORK_ERROR"

    def __init__(self, message: str = "", detail: JsonValue = None):
        self.message: str = message
        self.detail: JsonValue = detail
        super().__init__(message)
