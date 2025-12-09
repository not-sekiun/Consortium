from consortium.server.exceptions.base_consortium_exception import BaseConsortiumError


class BaseServiceException(BaseConsortiumError):
    """
    Base exception for all service related errors. This exception is meant to be used
    to catch and handle all errors that are raised from services across the application.

    Attributes:
        code: A **stable, machine-readable identifier** for the specific type of
            service error.
        message: A human-readable message that describes the error condition that
            occurred.
        detail: Any JSON-serializable data structure holding **structured, raw data**
            relevant to the failure.
    """
