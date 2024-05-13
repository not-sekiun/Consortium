from loguru import logger

from consortium.server.objects.agent_objects import Agent


class AgentsService:
    def __init__(self):
        self._agents = {}
        self._agents_service_logger = logger.bind(
            logger_name="Consortium Agents Service",
        )

    def create_agent(self, *args, **kwargs) -> Agent:
        agent = Agent(*args, **kwargs)
        self._agents[str(agent.agent_id)] = agent
        self._agents_service_logger.debug(
            f"Created agent: {agent!r}",
        )
        self._agents_service_logger.info(
            f"Created agent: {agent}",
        )
        return agent

    def remove_agent_by_agent_id(self, agent_id: str) -> None:
        try:
            agent = self._agents[agent_id]
        except KeyError:
            raise ValueError(f"No agent exists with the provided agent ID: {agent_id}")

        del self._agents[agent_id]
        self._agents_service_logger.debug(
            f"Removed agent: {agent!r}",
        )
        self._agents_service_logger.info(
            f"Removed agent: {agent}",
        )

    def get_agent_by_agent_id(self, agent_id: str) -> Agent:
        try:
            agent = self._agents[agent_id]
        except KeyError:
            raise ValueError(
                f"No agent exists with the provided agent ID: {agent_id}",
            )

        self._agents_service_logger.debug(
            f"Retrieved agent: {agent!r}",
        )
        self._agents_service_logger.info(
            f"Retrieved agent: {agent}",
        )
        return agent

    def get_all_agents(self) -> list[Agent]:
        all_agents = list(self._agents.values())
        self._agents_service_logger.debug(
            f"Retrieved all agents ({len(all_agents)} retrieved)",
        )
        return all_agents
