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
    code = "LISTENER_TEMPLATES_SERVICE_ERROR"


class ListenerTemplateNotFoundError(ListenerTemplatesServiceError):
    code = "LISTENER_TEMPLATE_NOT_FOUND_ERROR"

    def __init__(
        self,
        listener_template_id: str,
    ):
        super().__init__(
            message=(
                "Failed to find the requested listener template. No listener template "
                "could be found with the provided listener template ID "
                f"'{listener_template_id}'."
            ),
        )
