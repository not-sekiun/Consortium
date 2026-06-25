"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
"""

from typing import Any


class BaseConsortiumError(Exception):
    """
    Base exception for all errors that occur within Consortium.

    These exceptions are raised either by Consortium's core framework components or by
    services built on top of those components and are broadly grouped into either
    `<Domain>FrameworkError` or `<Domain>ServiceError` subclasses depending on
    they layer in which they originated.

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
