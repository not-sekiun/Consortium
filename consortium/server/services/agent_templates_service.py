import uuid

from loguru import logger

from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions import (
    AgentTemplateIDNotFoundError,
    AgentTemplateLabelNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.agent_profiles_service import AgentProfilesService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class AgentTemplatesService:
    def __init__(
        self,
        agent_profiles_service: AgentProfilesService,
    ):
        self._agent_profiles_service = agent_profiles_service
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self) -> str:
        return "Agent Templates Service"

    def __repr__(self) -> str:
        return (
            f"AgentTemplatesService("
            f"agent_profiles_service={self._agent_profiles_service!r}"
            f")"
        )

    @log_and_propagate_error_on_service_method
    def get_agent_template_by_agent_template_id(
        self,
        agent_template_id: str | uuid.UUID,
    ) -> BaseAgentTemplate:
        """Returns an agent template by its ID, searching across all loaded agent profiles.

        Args:
            agent_template_id (str | uuid.UUID): The ID of the agent template to
                retrieve.

        Returns:
            BaseAgentTemplate: The requested agent template.

        Raises:
            AgentTemplateIDNotFoundError: If no agent template with the given ID is found.
        """
        agent_template_id = normalize_uuid(agent_template_id)

        for agent_template in [
            agent_profile.agent_template
            for agent_profile in self._agent_profiles_service.get_all_agent_profiles()
        ]:
            if str(agent_template.agent_template_id) == agent_template_id:
                self._logger.debug(
                    "Retrieved agent template by agent template ID '{}': {!r}",
                    agent_template_id,
                    agent_template,
                )
                return agent_template
        raise AgentTemplateIDNotFoundError(
            agent_template_id=agent_template_id,
        )

    @log_and_propagate_error_on_service_method
    def get_agent_template_by_label(self, label: str) -> BaseAgentTemplate:
        """Returns an agent template by its label, searching across all loaded agent profiles.

        Args:
            label (str): The label of the agent template to retrieve.

        Returns:
            BaseAgentTemplate: The requested agent template.

        Raises:
            AgentTemplateLabelNotFoundError: If no agent template with the given label
                is found.
        """
        for agent_template in [
            agent_profile.agent_template
            for agent_profile in self._agent_profiles_service.get_all_agent_profiles()
        ]:
            if agent_template.label == label:
                self._logger.debug(
                    "Retrieved agent template by label '{}': {!r}",
                    label,
                    agent_template,
                )
                return agent_template
        raise AgentTemplateLabelNotFoundError(
            label=label,
        )

    @log_and_propagate_error_on_service_method
    def get_all_agent_templates(self) -> list[BaseAgentTemplate]:
        """Returns all agent templates across all loaded agent profiles.

        Returns:
            list[BaseAgentTemplate]: A list of all available agent templates. Empty if
                no agent profiles are loaded.
        """
        all_agent_templates = [
            agent_profile.agent_template
            for agent_profile in self._agent_profiles_service.get_all_agent_profiles()
        ]
        self._logger.debug(
            "Retrieved all agent templates ({} agent template(s) retrieved)",
            len(all_agent_templates),
        )
        return all_agent_templates
