from loguru import logger

from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.server.exceptions.service_exceptions.agent_templates_service_exceptions import (
    AgentTemplateNotFoundError,
)
from consortium.server.services.agent_profiles_service import AgentProfilesService


class AgentTemplatesService:
    def __init__(
        self,
        agent_profiles_service: AgentProfilesService,
    ):
        self._agent_profiles_service = agent_profiles_service
        self.agent_templates_service_logger = logger.bind(
            logger_name=str(self),
        )

    def __str__(self) -> str:
        return "Agent Templates Service"

    def __repr__(self) -> str:
        return "AgentTemplatesService()"

    def get_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
    ) -> BaseAgentTemplate:
        for agent_template in [
            agent_profile.agent_template
            for agent_profile in self._agent_profiles_service.get_all_agent_profiles()
        ]:
            if str(agent_template.agent_template_id) == agent_template_id:
                self.agent_templates_service_logger.debug(
                    f"Retrieved listener template: {agent_template!r}",
                )
                return agent_template
        raise AgentTemplateNotFoundError(
            agent_template_id=agent_template_id,
        )

    def get_all_agent_templates(self) -> list[BaseAgentTemplate]:
        all_agent_templates = [
            agent_profile.agent_template
            for agent_profile in self._agent_profiles_service.get_all_agent_profiles()
        ]
        self.agent_templates_service_logger.debug(
            f"Retrieved all listener templates ({len(all_agent_templates)}"
            f"listener template(s) retrieved).",
        )
        return all_agent_templates
