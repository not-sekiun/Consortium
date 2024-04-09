from loguru import logger

from consortium.server.framework.base_agent_generator import BaseAgentGenerator


class AgentGeneratorsService:
    def __init__(self):
        self._agent_generators = {}
        self._agent_generators_service_logger = logger.bind(
            logger_name="Consortium Listeners Service",
        )

    # Unlike user_accounts_service.py, we don't create the agent generator in this
    # method because we already have dedicated agent generator template objects that do
    # that for us
    def add_agent_generator(self, agent_generator: BaseAgentGenerator) -> None:
        if str(agent_generator.agent_generator_id) in self._agent_generators:
            raise ValueError(
                f"Cannot add agent generator to service because an agent generator with the same agent generator ID already exists: {agent_generator.agent_generator_id}",
            )

        self._agent_generators[str(agent_generator.agent_generator_id)] = (
            agent_generator
        )
        self._agent_generators_service_logger.debug(
            f"Added agent generator: {agent_generator!r}",
        )
        self._agent_generators_service_logger.info(
            f"Added agent generator: {agent_generator}",
        )

    def get_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> BaseAgentGenerator:
        try:
            agent_generator = self._agent_generators[agent_generator_id]
        except KeyError:
            raise ValueError(
                f"No agent generator exists with the provided agent generator ID: {agent_generator_id}",
            )

        self._agent_generators_service_logger.debug(
            f"Retrieved agent generator: {agent_generator!r}",
        )
        self._agent_generators_service_logger.info(
            f"Retrieved agent generator: {agent_generator}",
        )
        return agent_generator

    def get_all_agent_generators(self) -> list[BaseAgentGenerator]:
        all_agent_generators = list(self._agent_generators.values())
        self._agent_generators_service_logger.debug(
            f"Retrieved all agent_generators ({len(all_agent_generators)} retrieved)",
        )
        return all_agent_generators

    def remove_agent_generator(self, agent_generator: BaseAgentGenerator) -> None:
        try:
            del self._agent_generators[str(agent_generator.agent_generator_id)]
        except KeyError:
            raise ValueError(
                f"Agent generator does not exist: {agent_generator}",
            )

        self._agent_generators_service_logger.debug(
            f"Removed agent generator: {agent_generator!r}",
        )
        self._agent_generators_service_logger.info(
            f"Removed agent generator: {agent_generator}",
        )
