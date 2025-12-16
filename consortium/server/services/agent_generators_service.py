import copy
from typing import Any

from loguru import logger

from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.framework_exceptions import (
    agent_generators_framework_exceptions as agent_generators_framework_excs,
    agent_templates_framework_exceptions as agent_templates_framework_excs,
)
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.service_exceptions import (
    agent_generators_service_exceptions as agent_generators_svc_excs,
)
from consortium.server.objects.agent_generator_objects import AgentGeneratorState
from consortium.server.server_logging import LoggerType
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
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

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
            raise agent_generators_svc_excs.AgentGeneratorNotFoundError(
                agent_generator_id=agent_generator_id
            ) from None

        self._logger.debug(
            "Retrieved agent generator: {!r}",
            agent_generator,
        )
        return agent_generator

    def get_all_agent_generators(self) -> list[BaseAgentGenerator]:
        all_agent_generators = list(self._agent_generators.values())
        self._logger.debug(
            "Retrieved all agent_generators ({} retrieved)",
            len(all_agent_generators),
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

        try:
            agent_generator = agent_template.create_agent_generator(
                name=name,
                description=description,
                parameters=parameters,
            )
        except agent_templates_framework_excs.AgentTemplateOptionNotFoundError as exc:
            raise agent_generators_svc_excs.AgentTemplateOptionNotFoundError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except (
            agent_templates_framework_excs.AgentTemplateOptionValueValidationError
        ) as exc:
            raise agent_generators_svc_excs.AgentTemplateOptionValueValidationError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except (
            agent_templates_framework_excs.MissingRequiredAgentTemplateOptionError
        ) as exc:
            raise agent_generators_svc_excs.MissingRequiredAgentTemplateOptionError(
                message=exc.message,
                detail=exc.detail,
            ) from None

        self._agent_generators[str(agent_generator.agent_generator_id)] = (
            agent_generator
        )
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_CREATED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self._logger.info(
            "Created agent generator: {}",
            agent_generator,
        )
        self._logger.debug(
            "Created agent generator: {!r}",
            agent_generator,
        )
        return agent_generator

    async def add_agent_generator(self, agent_generator: BaseAgentGenerator) -> None:
        if str(agent_generator.agent_generator_id) in self._agent_generators:
            raise agent_generators_svc_excs.AgentGeneratorAlreadyExistsError(
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
        self._logger.info(
            "Added agent generator: {}",
            agent_generator,
        )
        self._logger.debug(
            "Added agent generator: {!r}",
            agent_generator,
        )

    async def remove_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        if agent_generator.status.state == AgentGeneratorState.RUNNING:
            raise agent_generators_svc_excs.AgentGeneratorAlreadyRunningError

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
        self._logger.info(
            "Removed agent generator: {}",
            removed_agent_generator,
        )
        self._logger.debug(
            "Removed agent generator: {!r}",
            removed_agent_generator,
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
        self._logger.info(
            "Updated name for agent generator {}: '{}' -> '{}'",
            agent_generator,
            old_name,
            name,
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
        self._logger.info(
            "Updated description for agent generator {}: '{}' -> '{}'",
            agent_generator,
            old_description,
            description,
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
            raise agent_generators_svc_excs.AgentGeneratorAlreadyRunningError

        for parameter_name, parameter_value in agent_generator.parameters.items():
            if parameter_name not in parameters:
                # `parameter_value` could be a list or a dict, so we need to perform
                # a deep copy to prevent reference sharing.
                parameters[parameter_name] = copy.deepcopy(parameter_value)

        for parameter_name, parameter_value in parameters.items():
            if parameter_name not in agent_generator.creating_agent_template.options:
                raise agent_generators_svc_excs.InvalidAgentGeneratorParameterNameError(
                    agent_generator=str(agent_generator),
                    parameter_name=parameter_name,
                )
            try:
                agent_generator.creating_agent_template.options[
                    parameter_name
                ].validate_value(value=parameter_value)
            except OptionValueValidationError as exc:
                raise agent_generators_svc_excs.InvalidAgentGeneratorParameterValueError(
                    agent_generator_str=str(agent_generator),
                    parameter_name=parameter_name,
                    parameter_value=str(parameter_value),
                    error_message=str(exc),
                ) from None
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
        self._logger.info(
            "Updated parameters for agent generators {} to {}",
            agent_generator,
            parameters,
        )
        self._logger.debug(
            "Updated parameters for agent generators {!r} to {}",
            agent_generator,
            parameters,
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
        except agent_generators_framework_excs.AgentGeneratorStartError as exc:
            raise agent_generators_svc_excs.AgentGeneratorStartError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except agent_generators_framework_excs.AgentGeneratorAlreadyRunningError as exc:
            raise agent_generators_svc_excs.AgentGeneratorAlreadyRunningError(
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
        except agent_generators_framework_excs.AgentGeneratorStopError as exc:
            raise agent_generators_svc_excs.AgentGeneratorStopError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except agent_generators_framework_excs.AgentGeneratorNotRunningError as exc:
            raise agent_generators_svc_excs.AgentGeneratorNotRunningError(
                message=exc.message
            ) from None

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
        except agent_generators_framework_excs.AgentGeneratorNotRunningError as exc:
            raise agent_generators_svc_excs.AgentGeneratorNotRunningError(
                message=exc.message
            ) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_CANCELLED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
