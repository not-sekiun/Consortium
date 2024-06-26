"""
Exception hierarchy for the listener templates service:

- BaseServiceException: Base class for all service-related exceptions.
 - ListenerTemplatesServiceError: Base class for all listener templates service
 exceptions.
   - ListenerTemplateIDNotFoundError: Listener template with provided ID not found.
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class ListenerTemplatesServiceError(BaseServiceException):
    def __init__(
        self,
        message: str = "An error occurred in the listener templates service.",
    ):
        super().__init__(message=message)


class ListenerTemplateNotFoundError(ListenerTemplatesServiceError):
    def __init__(
        self,
        listener_template_id: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to find the requested listener template. No listener template "
                "could be found with the provided listener template ID "
                f"'{listener_template_id}'."
            )
        super().__init__(message=message)
