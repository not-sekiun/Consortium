"""
Exception hierarchy for the agent templates service:

- BaseServiceException: Base class for all service-related exceptions.
 - AgentTemplatesServiceError: Base class for all agent templates service
 exceptions.
   - AgentTemplateNotFoundError: Agent template with provided ID not found.
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class AgentTemplatesServiceError(BaseServiceException):
    code = "AGENT_TEMPLATES_SERVICE_ERROR"


class AgentTemplateNotFoundError(AgentTemplatesServiceError):
    code = "AGENT_TEMPLATE_NOT_FOUND_ERROR"

    def __init__(
        self,
        agent_template_id: str,
    ):
        super().__init__(
            message=(
                "Failed to find the requested agent template. No agent template "
                "could be found with the provided agent template ID "
                f"'{agent_template_id}'."
            ),
        )
