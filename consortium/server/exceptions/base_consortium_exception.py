from typing import Any


class BaseConsortiumError(Exception):
    """
    Base exception for all Consortium errors that occur within the application.

    Both the `BaseFrameworkError` and `BaseServiceError` class of errors inherit from
    this exception. BaseAPIError does not inherit from this exception since API errors
    are meant to be handled separately by the REST API layer.

    Attributes:
        code: A **stable, machine-readable identifier** for the specific type of
            service error.
        message: A human-readable message that describes the error condition that
            occurred.
        detail: Any JSON-serializable data structure holding **structured, raw data**
            relevant to the failure.
    """

    code: str

    def __init__(self, message: str = "", detail: Any = None):
        self.message = message
        self.detail = detail
        super().__init__(message)
