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
        return agent

    #  def add_agent(self, agent: Agent) -> None:
    #  self._agents[str(agent.agent_id)] = agent

    def remove_agent_by_agent_id(self, agent_id: str) -> None:
        del self._agents[agent_id]

    def get_agent_by_agent_id(self, agent_id: str) -> Agent:
        return self._agents[agent_id]

    def get_all_agents(self) -> list[Agent]:
        return list(self._agents.values())
