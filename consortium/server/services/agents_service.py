from loguru import logger

from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
)
from consortium.server.objects.agent_objects import Agent


class AgentsService:
    def __init__(self):
        self._agents = {}
        self.agents_service_logger = logger.bind(
            logger_name=str(self),
        )

    def __str__(self) -> str:
        return "Consortium Agents Service"

    def __repr__(self) -> str:
        return "AgentsService()"

    def create_agent(self, *args, **kwargs) -> Agent:
        agent = Agent(*args, **kwargs)
        self._agents[str(agent.agent_id)] = agent
        self.agents_service_logger.info(f"Created agent: {agent}")
        self.agents_service_logger.debug(f"Created agent: {agent!r}")
        return agent

    def remove_agent_by_agent_id(self, agent_id: str) -> None:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)

        del self._agents[agent_id]
        self.agents_service_logger.info(f"Removed agent: {agent}")
        self.agents_service_logger.debug(f"Removed agent: {agent!r}")

    def get_agent_by_agent_id(self, agent_id: str) -> Agent:
        try:
            agent = self._agents[agent_id]
        except KeyError:
            raise AgentNotFoundError(agent_id=agent_id)

        self.agents_service_logger.info(f"Retrieved agent: {agent}")
        self.agents_service_logger.debug(f"Retrieved agent: {agent!r}")
        return agent

    def get_all_agents(self) -> list[Agent]:
        all_agents = list(self._agents.values())
        self.agents_service_logger.debug(
            f"Retrieved all agents ({len(all_agents)} retrieved)",
        )
        return all_agents
