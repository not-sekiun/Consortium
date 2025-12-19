from typing import Any


class BaseConsortiumError(Exception):
    """
    Base exception for all errors that occur within Consortium.

    Attributes:
        code: A **stable, machine-readable identifier** for the specific type of
            error that occurred.
        message: A human-readable message that describes the error.
        detail: Any JSON-serializable data structure holding **structured, raw data**
            relevant to the error.
    """

    code: str = "BASE_CONSORTIUM_ERROR"

    def __init__(self, message: str = "", detail: Any = None):
        self.message = message
        self.detail = detail
        super().__init__(message)
