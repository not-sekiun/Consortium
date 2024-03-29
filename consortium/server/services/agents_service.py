from loguru import logger

from consortium.server.objects.agent_objects import Agent


class AgentsService:
    def __init__(self):
        self._agents = {}
        self._agents_service_logger = logger.bind(
            logger_name="Consortium Agents Service",
        )

    def create_agent(self) -> Agent:
        agent = Agent()
        self._agents[str(agent.agent_id)] = agent
        self._agents_service_logger.info(
            f'Agent "{agent.agent_id}" was created',
        )
        return agent

    def remove_agent_by_agent_id(self, agent_id: str) -> None:
        try:
            del self._agents[agent_id]
        except KeyError:
            raise ValueError(f'Agent "{agent_id}" does not exist')

    def get_agent_by_agent_id(self, agent_id: str) -> Agent:
        return self._agents[agent_id]

    def get_all_agents(self) -> list[Agent]:
        all_agents = list(self._agents.values())
        self._agents_service_logger.debug(
            f"Retrieved all agents ({len(all_agents)} retrieved)",
        )
        return all_agents
