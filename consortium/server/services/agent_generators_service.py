import copy
from typing import Any

from loguru import logger

from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.framework.options.exceptions import OptionValueValidationError
from consortium.server.exceptions.framework_exceptions.agent_generators_framework_exceptions import (
    AgentGeneratorAlreadyRunningError as AgentGeneratorAlreadyRunningFrameworkError,
    AgentGeneratorNotRunningError as AgentGeneratorNotRunningFrameworkError,
    AgentGeneratorStartError as AgentGeneratorStartFrameworkError,
    AgentGeneratorStopError as AgentGeneratorStopFrameworkError,
)
from consortium.server.exceptions.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplateOptionNotFoundError as AgentTemplateOptionNotFoundFrameworkError,
    AgentTemplateOptionValueError as AgentTemplateOptionValueFrameworkError,
)
from consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions import (
    AgentGeneratorAlreadyExistsError,
    AgentGeneratorAlreadyRunningError as AgentGeneratorAlreadyRunningServiceError,
    AgentGeneratorNotFoundError,
    AgentGeneratorNotRunningError as AgentGeneratorNotRunningServiceError,
    AgentGeneratorStartError as AgentGeneratorStartServiceError,
    AgentGeneratorStopError as AgentGeneratorStopServiceError,
    AgentTemplateOptionNotFoundError as AgentTemplateOptionNotFoundServiceError,
    AgentTemplateOptionValueError as AgentTemplateOptionValueServiceError,
    InvalidAgentGeneratorParameterNameError,
    InvalidAgentGeneratorParameterValueError,
)
from consortium.server.objects.agent_generator_objects import AgentGeneratorState
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.events_service import EventsService


class AgentGeneratorsService:
    def __init__(
        self,
        agent_templates_service: AgentTemplatesService,
        events_service: EventsService,
    ):
        self._agent_templates_service = agent_templates_service
        self._events_service = events_service
        self._agent_generators = {}
        self.logger = logger.bind(logger_name=str(self))
        self.logger.debug(f"Started {self}")

    def __str__(self) -> str:
        return "Agent Generators Service"

    def __repr__(self) -> str:
        return (
            f"AgentGeneratorsService("
            f"agent_templates_service={self._agent_templates_service!r}"
            f")"
        )

    def get_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> BaseAgentGenerator:
        try:
            agent_generator = self._agent_generators[agent_generator_id]
        except KeyError:
            raise AgentGeneratorNotFoundError(agent_generator_id=agent_generator_id)

        self.logger.debug(
            f"Retrieved agent generator: {agent_generator!r}",
        )
        return agent_generator

    def get_all_agent_generators(self) -> list[BaseAgentGenerator]:
        all_agent_generators = list(self._agent_generators.values())
        self.logger.debug(
            f"Retrieved all agent_generators ({len(all_agent_generators)} retrieved)",
        )
        return all_agent_generators

    async def create_agent_generator_from_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
        parameters: dict[str, Any],
        name: str | None = None,
        description: str = "",
    ) -> BaseAgentGenerator:
        agent_template = (
            self._agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
            )
        )

        # for option_name, option_value in parameters.items():
        #     try:
        #         agent_template.set_option_value_by_option_name(
        #             option_name=option_name,
        #             option_value=option_value,
        #         )
        #     except AgentTemplateOptionNotFoundFrameworkError as exc:
        #         raise AgentTemplateOptionNotFoundServiceError(
        #             message=exc.message,
        #             detail=exc.detail,
        #         )
        #     except AgentTemplateOptionValueFrameworkError as exc:
        #         raise AgentTemplateOptionValueServiceError(
        #             message=exc.message,
        #             detail=exc.detail,
        #         )

        try:
            agent_generator = agent_template.create_agent_generator(
                name=name,
                description=description,
                parameters=parameters,
            )
        except AgentTemplateOptionNotFoundFrameworkError as exc:
            raise AgentTemplateOptionNotFoundServiceError(
                message=exc.message,
                detail=exc.detail,
            )
        except AgentTemplateOptionValueFrameworkError as exc:
            raise AgentTemplateOptionValueServiceError(
                message=exc.message,
                detail=exc.detail,
            )

        # agent_template.clear_all_option_values()
        self._agent_generators[str(agent_generator.agent_generator_id)] = (
            agent_generator
        )
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_CREATED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self.logger.info(
            "Created agent generator: {}",
            agent_generator,
        )
        self.logger.debug(
            "Created agent generator: {!r}",
            agent_generator,
        )
        return agent_generator

    async def add_agent_generator(self, agent_generator: BaseAgentGenerator) -> None:
        if str(agent_generator.agent_generator_id) in self._agent_generators:
            raise AgentGeneratorAlreadyExistsError(
                agent_generator_id=str(agent_generator.agent_generator_id),
            )

        self._agent_generators[str(agent_generator.agent_generator_id)] = (
            agent_generator
        )
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_ADDED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self.logger.info(
            f"Added agent generator: {agent_generator}",
        )
        self.logger.debug(
            f"Added agent generator: {agent_generator!r}",
        )

    async def remove_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        if agent_generator.status.state == AgentGeneratorState.RUNNING:
            raise AgentGeneratorAlreadyRunningServiceError

        removed_agent_generator = self._agent_generators.pop(agent_generator_id)
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_REMOVED,
                data={
                    "agent_generator_id": str(
                        removed_agent_generator.agent_generator_id,
                    ),
                },
            ),
        )
        self.logger.info(
            f"Removed agent generator: {removed_agent_generator}",
        )
        self.logger.debug(
            f"Removed agent generator: {removed_agent_generator!r}",
        )

    async def update_agent_generator_name_by_agent_generator_id(
        self,
        agent_generator_id: str,
        name: str,
    ) -> BaseAgentGenerator:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        old_name = agent_generator.name
        agent_generator.name = name
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_UPDATED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self.logger.info(
            f"Updated name for agent generator {agent_generator}: '{old_name}' -> '{name}'",
        )
        return agent_generator

    async def update_agent_generator_description_by_agent_generator_id(
        self,
        agent_generator_id: str,
        description: str,
    ) -> BaseAgentGenerator:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        old_description = agent_generator.description
        agent_generator.description = description
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_UPDATED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self.logger.info(
            f"Updated description for agent generator {agent_generator}: '{old_description}' -> '{description}'",
        )
        return agent_generator

    async def update_agent_generator_parameters_by_agent_generator_id(
        self,
        agent_generator_id: str,
        parameters: dict[str, Any],
    ) -> BaseAgentGenerator:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )

        if agent_generator.status.state == AgentGeneratorState.RUNNING:
            raise AgentGeneratorAlreadyRunningServiceError

        for parameter_name, parameter_value in agent_generator.parameters.items():
            if parameter_name not in parameters:
                # `parameter_value` could be a list or a dict, so we need to perform
                # a deep copy to prevent reference sharing.
                parameters[parameter_name] = copy.deepcopy(parameter_value)

        for parameter_name, parameter_value in parameters.items():
            if parameter_name not in agent_generator.creating_agent_template.options:
                raise InvalidAgentGeneratorParameterNameError(
                    agent_generator_str=str(agent_generator),
                    parameter_name=parameter_name,
                )
            try:
                agent_generator.creating_agent_template.options[
                    parameter_name
                ].validate_value(value=parameter_value)
            except OptionValueValidationError as exc:
                raise InvalidAgentGeneratorParameterValueError(
                    agent_generator_str=str(agent_generator),
                    parameter_name=parameter_name,
                    parameter_value=str(parameter_value),
                    validation_error_message=str(exc),
                )
            parameters[parameter_name] = parameter_value

        # Create a temporary agent generator whose attributes we copy over to the
        # existing agent generator. This allows us to perform the name and
        # endpoint resolution required to update the attribute without
        # inadvertently overwriting any existing state within the existing
        # agent generator.
        temporary_agent_generator = (
            agent_generator.creating_agent_template.create_agent_generator(
                parameters=parameters,
            )
        )
        agent_generator.name = temporary_agent_generator.name
        agent_generator.parameters = copy.deepcopy(temporary_agent_generator.parameters)

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_UPDATED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self.logger.info(
            f"Updated parameters for agent generators {agent_generator} to {parameters}",
        )
        self.logger.debug(
            f"Updated parameters for agent generators {agent_generator!r} to {parameters}",
        )
        return agent_generator

    async def start_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        try:
            await agent_generator.start()
        except AgentGeneratorStartFrameworkError as exc:
            raise AgentGeneratorStartServiceError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except AgentGeneratorAlreadyRunningFrameworkError as exc:
            raise AgentGeneratorAlreadyRunningServiceError(
                message=exc.message,
            ) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_STARTED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )

    async def stop_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        try:
            await agent_generator.stop()
        except AgentGeneratorStopFrameworkError as exc:
            raise AgentGeneratorStopServiceError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except AgentGeneratorNotRunningFrameworkError as exc:
            raise AgentGeneratorNotRunningServiceError(message=exc.message) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_STOPPED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )

    async def cancel_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        try:
            await agent_generator.cancel()
        except AgentGeneratorNotRunningFrameworkError as exc:
            raise AgentGeneratorNotRunningServiceError(message=exc.message) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_CANCELLED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
