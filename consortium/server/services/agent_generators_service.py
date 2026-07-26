import copy
import uuid
from typing import Any

from loguru import logger

from consortium.framework._core.components.component_status import State
from consortium.framework._core.framework_exceptions.agent_generators_framework_exceptions import (
    AgentGeneratorAlreadyRunningError,
)
from consortium.framework._core.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions import (
    AgentGeneratorAlreadyExistsError,
    AgentGeneratorNotFoundError,
    InvalidAgentGeneratorParameterNameError,
    InvalidAgentGeneratorParameterValueError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.events_service import EventsService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
    run_async_background_task,
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
        """Returns an agent generator by its ID.

        Args:
            agent_generator_id: The ID of the agent generator to
                retrieve.

        Returns:
            The requested agent generator.

        Raises:
            AgentGeneratorNotFoundError: If no agent generator with the given ID exists.
        """
        agent_generator_id = normalize_uuid(agent_generator_id)

        try:
            agent_generator = self._agent_generators[agent_generator_id]
        except KeyError:
            raise AgentGeneratorNotFoundError(
                agent_generator_id=agent_generator_id
            ) from None

        self._logger.debug(
            "Retrieved agent generator: {!r}",
            agent_generator,
        )
        return agent_generator

    @log_and_propagate_error_on_service_method
    def get_all_agent_generators(self) -> list[BaseAgentGenerator]:
        """Returns all agent generators currently held by the service.

        Returns:
            A list of all agent generators. Empty if none exist.
        """
        all_agent_generators = list(self._agent_generators.values())
        self._logger.debug(
            "Retrieved all agent_generators ({} retrieved)",
            len(all_agent_generators),
        )
        return all_agent_generators

    @log_and_propagate_error_on_service_method
    def create_agent_generator_from_agent_template_by_agent_template_id(
        self,
        agent_template_id: str | uuid.UUID,
        parameters: dict[str, Any],
        name: str | None = None,
        description: str = "",
    ) -> BaseAgentGenerator:
        """Creates and registers a new agent generator from the specified agent template.

        Emits an `AGENT_GENERATOR_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to create
                the agent generator from.
            parameters: Build parameters to pass to the agent template
                when creating the agent generator.
            name: An optional display name for the new agent generator.
                If omitted, the name is derived from the template.
            description: An optional description for the new agent generator.

        Returns:
            The newly created agent generator instance.

        Raises:
            AgentTemplateIDNotFoundError: If no agent template with the given ID is found.
            InvalidAgentGeneratorParameterNameError: If a parameter name is not valid for
                the agent template.
            InvalidAgentGeneratorParameterValueError: If a parameter value fails
                validation against the agent template.
        """
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
        self._agent_generators[str(agent_generator.agent_generator_id)] = (
            agent_generator
        )

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_GENERATOR_CREATED,
                message=f"Created agent generator: {agent_generator}",
                data=agent_generator.to_json(),
            )
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
    def add_agent_generator(self, agent_generator: BaseAgentGenerator) -> None:
        """Adds an already-instantiated agent generator to the service.

        Unlike `create_agent_generator_from_agent_template_by_agent_template_id`, this
        method accepts a pre-built agent generator instance rather than creating one from
        a template. Emits an `AGENT_GENERATOR_ADDED` event.

        Args:
            agent_generator: The agent generator instance to add.

        Raises:
            AgentGeneratorAlreadyExistsError: If an agent generator with the same ID is
                already registered.
        """
        if str(agent_generator.agent_generator_id) in self._agent_generators:
            raise AgentGeneratorAlreadyExistsError(
                agent_generator_id=str(agent_generator.agent_generator_id),
            )

        self._agent_generators[str(agent_generator.agent_generator_id)] = (
            agent_generator
        )

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_GENERATOR_ADDED,
                message=f"Added agent generator: {agent_generator}",
                data=agent_generator.to_json(),
            )
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
    def remove_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
    ) -> None:
        """Removes an agent generator from the service.

        Emits an `AGENT_GENERATOR_REMOVED` event. The agent generator must not currently
        be running; stop it first before removing.

        Args:
            agent_generator_id: The ID of the agent generator to
                remove.

        Raises:
            AgentGeneratorNotFoundError: If no agent generator with the given ID exists.
            AgentGeneratorAlreadyRunningError: If the agent generator is currently
                running.
        """
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
        if agent_generator.status.state == State.RUNNING:
            raise AgentGeneratorAlreadyRunningError(
                component_str=str(agent_generator),
            )

        removed_agent_generator = self._agent_generators.pop(
            str(agent_generator.agent_generator_id)
        )

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_GENERATOR_REMOVED,
                message=f"Removed agent generator: {removed_agent_generator}",
                data=removed_agent_generator.to_json(),
            )
        )
        self._logger.info("Removed agent generator: {}", removed_agent_generator)
        self._logger.debug("- {!r}", removed_agent_generator)

    @log_and_propagate_error_on_service_method
    def update_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> BaseAgentGenerator:
        """Updates the name, description, and/or parameters of an agent generator.

        Parameter updates are applied atomically: if validation of any parameter fails,
        no other updates are applied. When `parameters` is provided, missing keys are
        back-filled from the existing parameter set so only the specified fields change.
        Emits an `AGENT_GENERATOR_UPDATED` event when at least one field changes.

        Args:
            agent_generator_id: The ID of the agent generator to
                update.
            name: The new display name. When `None`, the name is not
                changed.
            description: The new description. When `None`, the description
                is not changed.
            parameters: A partial or full mapping of parameter
                names to new values. When `None`, parameters are not changed.

        Returns:
            The updated agent generator instance.

        Raises:
            AgentGeneratorNotFoundError: If no agent generator with the given ID exists.
            AgentGeneratorAlreadyRunningError: If a parameter update is attempted while
                the agent generator is running.
            InvalidAgentGeneratorParameterNameError: If a key in `parameters` is not a
                valid parameter for the creating agent template.
            InvalidAgentGeneratorParameterValueError: If a value in `parameters` fails
                validation against the creating agent template.
        """
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
            if agent_generator.status.state == State.RUNNING:
                raise AgentGeneratorAlreadyRunningError(
                    component_str=str(agent_generator),
                )

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
                # inadvertently overwriting any existing status within the existing
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
                    "Updated parameters for agent generator {}",
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
                "Updated name for agent generator {} from '{}' to '{}'",
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
                "Updated description for agent generator {} from '{}' to '{}'",
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
            run_async_background_task(
                coroutine=self._events_service.trigger_event(
                    event_type=EventType.AGENT_GENERATOR_UPDATED,
                    message=f"Updated agent generator: {agent_generator}",
                    data={
                        "agent_generator": agent_generator.to_json(),
                        "updated": updated,
                    },
                )
            )
        else:
            self._logger.debug(
                "No updates applied to agent generator {!r} as no changes were detected "
                "even though the update method was called",
                agent_generator,
            )

        return agent_generator

    @log_and_propagate_error_on_service_method
    async def start_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
        blocking: bool = False,
    ) -> None:
        """Starts an agent generator by its ID.

        Emits an `AGENT_GENERATOR_STARTED` event after starting.

        Args:
            agent_generator_id: The ID of the agent generator to
                start.
            blocking: If `True`, waits until the agent generator has fully
                started before returning. Defaults to `False`.

        Raises:
            AgentGeneratorNotFoundError: If no agent generator with the given ID exists.
        """
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )

        await agent_generator.start()
        if blocking:
            await agent_generator.wait_until_started()

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_GENERATOR_STARTED,
                message=f"Started agent generator: {agent_generator}",
                data=agent_generator.to_json(),
            )
        )
        self._logger.info("Started agent generator: {}", agent_generator)
        self._logger.debug("- {!r}", agent_generator)

    @log_and_propagate_error_on_service_method
    async def stop_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
        blocking: bool = False,
    ) -> None:
        """Stops an agent generator by its ID.

        Emits an `AGENT_GENERATOR_STOPPED` event after stopping.

        Args:
            agent_generator_id: The ID of the agent generator to
                stop.
            blocking: If `True`, waits until the agent generator has fully
                stopped before returning. Defaults to `False`.

        Raises:
            AgentGeneratorNotFoundError: If no agent generator with the given ID exists.
        """
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )

        await agent_generator.stop()
        if blocking:
            await agent_generator.wait_until_stopped()

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_GENERATOR_STOPPED,
                message=f"Stopped agent generator: {agent_generator}",
                data=agent_generator.to_json(),
            )
        )
        self._logger.info("Stopped agent generator: {}", agent_generator)
        self._logger.debug("- {!r}", agent_generator)

    @log_and_propagate_error_on_service_method
    async def cancel_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str | uuid.UUID,
        blocking: bool = False,
    ) -> None:
        """Cancels an agent generator by its ID, forcibly aborting it.

        Unlike stopping, cancellation does not wait for the agent generator to finish
        its current operation cleanly. Emits an `AGENT_GENERATOR_CANCELLED` event.

        Args:
            agent_generator_id: The ID of the agent generator to
                cancel.
            blocking: If `True`, waits until the agent generator has fully
                stopped before returning. Defaults to `False`.

        Raises:
            AgentGeneratorNotFoundError: If no agent generator with the given ID exists.
        """
        agent_generator = self.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )

        await agent_generator.cancel()
        if blocking:
            await agent_generator.wait_until_stopped()

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_GENERATOR_CANCELLED,
                message=f"Cancelled agent generator: {agent_generator}",
                data=agent_generator.to_json(),
            )
        )
        self._logger.info("Cancelled agent generator: {}", agent_generator)
        self._logger.debug("- {!r}", agent_generator)
