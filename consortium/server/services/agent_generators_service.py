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
                f'Listener "{agent_generator.name}" ({agent_generator.agent_generator_id}) already exists',
            )

        self._agent_generators[str(agent_generator.agent_generator_id)] = (
            agent_generator
        )
        self._agent_generators_service_logger.info(
            f'Listener "{agent_generator.name}" ({agent_generator.agent_generator_id}) was created',
        )

    def get_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> BaseAgentGenerator:
        try:
            agent_generator = self._agent_generators[agent_generator_id]
        except KeyError:
            raise ValueError(
                f'Listener with the agent_generator ID "{agent_generator_id}" does not exist',
            )

        self._agent_generators_service_logger.debug(
            f'Retrieved agent_generator "{agent_generator.name}" ({agent_generator_id})',
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
                f'Listener "{agent_generator.name}" ({agent_generator.agent_generator_id}) does not exist',
            )

        self._agent_generators_service_logger.info(
            f'Listener "{agent_generator.name}" ({agent_generator.agent_generator_id}) was removed',
        )
