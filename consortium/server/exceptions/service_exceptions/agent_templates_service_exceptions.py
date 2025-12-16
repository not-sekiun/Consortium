"""
Exception hierarchy for the agent templates service.

- [BaseServiceException][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceException]
    - [AgentTemplatesServiceError][consortium.server.exceptions.service_exceptions.agent_templates_service_exceptions.AgentTemplatesServiceError]
        - [AgentTemplateNotFoundError][consortium.server.exceptions.service_exceptions.agent_templates_service_exceptions.AgentTemplateNotFoundError]
            - [AgentTemplateIDNotFoundError][consortium.server.exceptions.service_exceptions.agent_templates_service_exceptions.AgentTemplateIDNotFoundError]
            - [AgentTemplateLabelNotFoundError][consortium.server.exceptions.service_exceptions.agent_templates_service_exceptions.AgentTemplateLabelNotFoundError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class AgentTemplatesServiceError(BaseServiceException):
    """
    Base exception for all agent templates service errors.
    """

    code = "AGENT_TEMPLATES_SERVICE_ERROR"


class AgentTemplateNotFoundError(AgentTemplatesServiceError):
    """
    Raised when the requested agent template is not found.
    """

    code = "AGENT_TEMPLATE_NOT_FOUND_ERROR"


class AgentTemplateIDNotFoundError(AgentTemplatesServiceError):
    """
    Raised when the requested agent template with the provided agent template ID was
    not found.

    Args:
        agent_template_id (str): The agent template ID that was not found.
    """

    code = "AGENT_TEMPLATE_ID_NOT_FOUND_ERROR"

    def __init__(self, agent_template_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent template. No agent template was "
                f"found with the provided agent template ID '{agent_template_id}'."
            ),
            detail={"agent_template_id": agent_template_id},
        )


class AgentTemplateLabelNotFoundError(AgentTemplatesServiceError):
    """
    Raised when the requested agent template with the provided label was not found.

    Args:
        label (str): The agent template label that was not found.
    """

    code = "AGENT_TEMPLATE_LABEL_NOT_FOUND_ERROR"

    def __init__(self, label: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent template. No agent template was "
                f"found with the provided label '{label}'."
            ),
            detail={"label": label},
        )
