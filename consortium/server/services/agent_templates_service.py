from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.framework.base_agent_template import BaseAgentTemplate


class AgentTemplatesService:
    def __init__(self):
        self.agent_templates_service_logger = logger.bind(
            logger_name=str(self),
        )

    def __str__(self) -> str:
        return "Consortium Agent Templates Service"

    def __repr__(self) -> str:
        return "AgentTemplatesService()"

    def get_all_agent_templates(
        self,
    ) -> list[BaseAgentTemplate]:
        all_agent_templates = [
            agent_profile.agent_template
            for agent_profile in server_singletons.agent_profiles_service.get_all_agent_profiles()
        ]
        self.agent_templates_service_logger.debug(
            f"Retrieved all agent templates ({len(all_agent_templates)} retrieved)",
        )
        return all_agent_templates

    def get_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
    ) -> BaseAgentTemplate:
        for agent_template in self.get_all_agent_templates():
            if str(agent_template.agent_template_id) == agent_template_id:
                self.agent_templates_service_logger.debug(
                    f"Retrieved agent template: {agent_template!r}",
                )
                return agent_template
        raise ValueError(
            f"No agent template exists with the provided agent template ID: "
            f"{agent_template_id}",
        )
