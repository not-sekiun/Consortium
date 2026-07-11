"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`AgentTemplatesError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplatesError]
        - [`AgentTemplatesServiceError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplatesServiceError]
            - [`AgentTemplateNotFoundError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateNotFoundError]
                - [`AgentTemplateIDNotFoundError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateIDNotFoundError]
                - [`AgentTemplateLabelNotFoundError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateLabelNotFoundError]
"""
# TODO: The docstring generator tool for some reason missed out on InvalidFrameworkVersionSpecifierError agent template, listener template, event hooks and plugins exceptions

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class AgentTemplatesError(BaseConsortiumError):
    """Base exception for all agent templates-related errors."""

    code = "AGENT_TEMPLATES_ERROR"


class AgentTemplatesServiceError(AgentTemplatesError):
    """Base exception for all errors that occur within the agent templates service."""

    code = "AGENT_TEMPLATES_SERVICE_ERROR"


class AgentTemplateNotFoundError(AgentTemplatesServiceError):
    """Raised when the requested agent template was not found in the agent templates
    service.
    """

    code = "AGENT_TEMPLATE_NOT_FOUND_ERROR"


class AgentTemplateIDNotFoundError(AgentTemplateNotFoundError):
    """Raised when the requested agent template with the provided agent template ID was
    not found in the agent templates service.
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


class AgentTemplateLabelNotFoundError(AgentTemplateNotFoundError):
    """Raised when the requested agent template with the provided label was not found in
    the agent templates service.
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
