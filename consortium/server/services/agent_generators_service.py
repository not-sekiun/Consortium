import copy
import uuid
from typing import Any

from loguru import logger

from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.framework_exceptions import (
    agent_generators_framework_exceptions as framework_excs,
    # agent_templates_framework_exceptions as agent_templates_framework_excs,
)
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.service_exceptions import (
    agent_generators_service_exceptions as svc_excs,
)
from consortium.server.objects.agent_generator_objects import AgentGeneratorState
from consortium.server.server_logging import LoggerType
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.events_service import EventsService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


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

    @log_and_propagate_error_on_service_method
    def get_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
    ) -> BaseAgentGenerator:
        agent_generator_id = normalize_uuid(agent_generator_id)
        try:
            agent_generator = self._agent_generators[agent_generator_id]
        except KeyError:
            raise svc_excs.AgentGeneratorNotFoundError(
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

    @log_and_propagate_error_on_service_method
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

        agent_generator = agent_template.create_agent_generator(
            name=name,
            description=description,
            parameters=parameters,
        )
        # try:
        #     agent_generator = agent_template.create_agent_generator(
        #         name=name,
        #         description=description,
        #         parameters=parameters,
        #     )
        # except agent_templates_framework_excs.AgentTemplateOptionNotFoundError as exc:
        #     raise svc_excs.AgentTemplateOptionNotFoundError(
        #         message=exc.message,
        #         detail=exc.detail,
        #     ) from None
        # except (
        #     agent_templates_framework_excs.AgentTemplateOptionValueValidationError
        # ) as exc:
        #     raise svc_excs.AgentTemplateOptionValueValidationError(
        #         message=exc.message,
        #         detail=exc.detail,
        #     ) from None
        # except (
        #     agent_templates_framework_excs.MissingRequiredAgentTemplateOptionError
        # ) as exc:
        #     raise svc_excs.MissingRequiredAgentTemplateOptionError(
        #         message=exc.message,
        #         detail=exc.detail,
        #     ) from None

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
            "- {!r}",
            agent_generator,
        )
        return agent_generator

    @log_and_propagate_error_on_service_method
    async def add_agent_generator(self, agent_generator: BaseAgentGenerator) -> None:
        if str(agent_generator.agent_generator_id) in self._agent_generators:
            raise svc_excs.AgentGeneratorAlreadyExistsError(
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
            "- {!r}",
            agent_generator,
        )

    @log_and_propagate_error_on_service_method
    async def remove_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        if agent_generator.status.state == AgentGeneratorState.RUNNING:
            raise framework_excs.AgentGeneratorAlreadyRunningError

        removed_agent_generator = self._agent_generators.pop(
            agent_generator.agent_generator_id
        )
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
        self._logger.info("Removed agent generator: {}", removed_agent_generator)
        self._logger.debug("- {!r}", removed_agent_generator)

    @log_and_propagate_error_on_service_method
    async def update_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> BaseAgentGenerator:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id
        )

        # Changed dictionary is used to track what attributes were updated. This data
        # is sent as part of the `AGENT_GENERATOR_UPDATED` event.
        updated = {}

        # Update parameters first before updating name and description. This is because
        # updating parameters may also update the name (if the name is derived from
        # parameters). But if the name is provided explicitly, it will overwrite any
        # name derived from parameters. Also, if parameter validation raises an error
        # it prevents any other updates from being applied maintaining atomicity.
        if parameters is not None:
            # Hold a list of fields that are being updated for logging purposes later
            # on. This makes a copy of the parameter keys being updated.
            updated_fields = list(parameters)

            # Cannot update running agent generators because the parameters change wont be
            # reflected in the agent generator.
            if agent_generator.status.state == AgentGeneratorState.RUNNING:
                raise framework_excs.AgentGeneratorAlreadyRunningError

            # Fill in any missing parameters with values from the existing set of
            # parameters.
            for parameter_name, parameter_value in agent_generator.parameters.items():
                if parameter_name not in parameters:
                    # `parameter_value` could be a list or a dict, so we need to perform
                    # a deep copy to prevent reference sharing.
                    parameters[parameter_name] = copy.deepcopy(parameter_value)

            # Perform validation of `parameters` if they are being updated.
            for parameter_name, parameter_value in parameters.items():
                if (
                    parameter_name
                    not in agent_generator.creating_agent_template.options
                ):
                    raise svc_excs.InvalidAgentGeneratorParameterNameError(
                        agent_generator=str(agent_generator),
                        parameter_name=parameter_name,
                    )
                try:
                    agent_generator.creating_agent_template.options[
                        parameter_name
                    ].validate_value(value=parameter_value)
                except OptionValueValidationError as exc:
                    raise svc_excs.InvalidAgentGeneratorParameterValueError(
                        agent_generator_str=str(agent_generator),
                        parameter_name=parameter_name,
                        parameter_value=str(parameter_value),
                        error_message=str(exc),
                    ) from None
                parameters[parameter_name] = parameter_value

            if parameters == agent_generator.parameters:
                # No parameter changes so skip updating.
                pass
            else:
                # Create a temporary agent generator whose attributes we copy over to the
                # existing agent generator. This allows us to perform the `name`
                # resolution required to update the attribute without
                # inadvertently overwriting any existing state within the existing
                # agent generator.
                temp_agent_generator = (
                    agent_generator.creating_agent_template.create_agent_generator(
                        parameters=parameters,
                    )
                )
                agent_generator.name = temp_agent_generator.name
                old_parameters = copy.deepcopy(agent_generator.parameters)
                agent_generator.parameters = copy.deepcopy(
                    temp_agent_generator.parameters
                )
                updated["parameters"] = {
                    "old": old_parameters,  # `old_parameters` is already a deep copy
                    "new": copy.deepcopy(agent_generator.parameters),
                }
                self._logger.info(
                    "Updated parameters for agent generator {}.",
                    agent_generator,
                )
                for parameter_name in updated_fields:
                    self._logger.info(
                        "- Updated parameter '{}' from {!r} to {!r}",
                        parameter_name,
                        old_parameters[parameter_name],
                        agent_generator.parameters[parameter_name],
                    )
                self._logger.debug("- {!r}", agent_generator)

        if name is not None and name != agent_generator.name:
            old_name = agent_generator.name
            agent_generator.name = name
            self._logger.info(
                "Updated name for agent generator {} from '{}' to '{}'.",
                agent_generator,
                old_name,
                name,
            )
            self._logger.debug("- {!r}", agent_generator)
            updated["name"] = {
                "old": old_name,
                "new": name,
            }

        if description is not None and description != agent_generator.description:
            old_description = agent_generator.description
            agent_generator.description = description
            self._logger.info(
                "Updated description for agent generator {} from '{}' to '{}'.",
                agent_generator,
                old_description,
                description,
            )
            self._logger.debug("- {!r}", agent_generator)
            updated["description"] = {
                "old": old_description,
                "new": description,
            }

        # Only fire events for meaningful changes, skip firing if a no-op update
        # occurred.
        if updated:
            await self._events_service.trigger_event(
                event=Event(
                    event_type=EventType.AGENT_GENERATOR_UPDATED,
                    data={
                        "agent_generator_id": str(agent_generator.agent_generator_id),
                        "updated": updated,
                    },
                ),
            )
        else:
            self._logger.debug(
                "No updates applied to agent generator {!r} as no changes were detected "
                "even though the update method was called.",
                agent_generator,
            )

        return agent_generator

    @log_and_propagate_error_on_service_method
    async def start_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )

        await agent_generator.start()
        # try:
        #     await agent_generator.start()
        # except framework_excs.AgentGeneratorStartError as exc:
        #     raise svc_excs.AgentGeneratorStartError(
        #         message=exc.message,
        #         detail=exc.detail,
        #     ) from None
        # except framework_excs.AgentGeneratorAlreadyRunningError as exc:
        #     raise svc_excs.AgentGeneratorAlreadyRunningError(
        #         message=exc.message,
        #     ) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_STARTED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self._logger.info("Started agent generator: {}", agent_generator)
        self._logger.debug("- {!r}", agent_generator)

    @log_and_propagate_error_on_service_method
    async def stop_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )

        await agent_generator.stop()
        # try:
        #     await agent_generator.stop()
        # except framework_excs.AgentGeneratorStopError as exc:
        #     raise svc_excs.AgentGeneratorStopError(
        #         message=exc.message,
        #         detail=exc.detail,
        #     ) from None
        # except framework_excs.AgentGeneratorNotRunningError as exc:
        #     raise svc_excs.AgentGeneratorNotRunningError(
        #         message=exc.message
        #     ) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_STOPPED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self._logger.info("Stopped agent generator: {}", agent_generator)
        self._logger.debug("- {!r}", agent_generator)

    @log_and_propagate_error_on_service_method
    async def cancel_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
    ) -> None:
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )

        await agent_generator.cancel()
        # try:
        #     await agent_generator.cancel()
        # except framework_excs.AgentGeneratorNotRunningError as exc:
        #     raise svc_excs.AgentGeneratorNotRunningError(
        #         message=exc.message
        #     ) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_GENERATOR_CANCELLED,
                data={"agent_generator_id": str(agent_generator.agent_generator_id)},
            ),
        )
        self._logger.info("Cancelled agent generator: {}", agent_generator)
        self._logger.debug("- {!r}", agent_generator)
