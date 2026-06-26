import asyncio
import copy
import uuid
from typing import Any

from loguru import logger
from pydantic import validate_call

from consortium.framework._components._component_status import State
from consortium.framework.event_hooks.event_type import EventType
from consortium.framework.listeners.base_listener import BaseListener
from consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions import (
    InvalidListenerParameterNameError,
    InvalidListenerParameterValueError,
    ListenerAlreadyExistsError,
    ListenerAlreadyRunningError,
    ListenerNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    OptionValueValidationError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.events_service import EventsService
from consortium.server.services.listener_templates_service import (
    ListenerTemplatesService,
)
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class ListenersService:
    def __init__(
        self,
        listener_templates_service: ListenerTemplatesService,
        events_service: EventsService,
    ):
        self._listener_templates_service = listener_templates_service
        self._events_service = events_service
        self._listeners = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Listeners Service"

    def __repr__(self) -> str:
        return (
            f"ListenersService("
            f"listener_templates_service={self._listener_templates_service!r}"
            f")"
        )

    @log_and_propagate_error_on_service_method
    @validate_call
    def get_listener_by_listener_id(self, listener_id: str | uuid.UUID) -> BaseListener:
        """Gets a listener by its ID.

        Args:
            listener_id (str | uuid.UUID): The ID of the listener to retrieve.

        Returns:
            BaseListener: The requested listener.

        Raises:
            ListenerNotFoundError: If no listener with the given ID exists.
        """
        listener_id = normalize_uuid(listener_id)

        try:
            listener = self._listeners[listener_id]
        except KeyError:
            raise ListenerNotFoundError(listener_id=listener_id) from None
        self._logger.debug("Retrieved listener: {!r}", listener)
        return listener

    @log_and_propagate_error_on_service_method
    def get_all_listeners(self) -> list[BaseListener]:
        """Gets all registered listeners.

        Returns:
            list[BaseListener]: A list of all listeners.
        """
        all_listeners = list(self._listeners.values())
        self._logger.debug(
            "Retrieved all listeners ({} retrieved)",
            len(all_listeners),
        )
        return all_listeners

    @log_and_propagate_error_on_service_method
    def create_listener_from_listener_template_by_listener_template_id(
        self,
        listener_template_id: str | uuid.UUID,
        parameters: dict[str, Any],
        name: str | None = None,
        description: str = "",
    ) -> BaseListener:
        """Creates a listener from a listener template.

        Args:
            listener_template_id (str | uuid.UUID): The ID of the listener template to use.
            parameters (dict[str, Any]): The parameters for the new listener.
            name (str | None, optional): The name of the new listener. Defaults to None.
            description (str, optional): The description of the new listener. Defaults to "".

        Returns:
            BaseListener: The newly created listener.

        Raises:
            ListenerTemplateNotFoundError: If the specified listener template does not exist.
        """
        listener_template = self._listener_templates_service.get_listener_template_by_listener_template_id(
            listener_template_id=listener_template_id,
        )

        listener = listener_template.create_listener(
            name=name,
            description=description,
            parameters=parameters,
        )
        self._listeners[str(listener.listener_id)] = listener
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.LISTENER_CREATED,
                message=f"Created listener: {listener}",
                data=listener.to_json(),
            )
        )
        self._logger.info("Created listener: {}", listener)
        self._logger.debug("- {!r}", listener)

        return listener

    @log_and_propagate_error_on_service_method
    def add_listener(self, listener: BaseListener) -> None:
        """Adds an existing listener to the service.

        Args:
            listener (BaseListener): The listener to add.

        Raises:
            ListenerAlreadyExistsError: If a listener with the same ID already exists.
        """
        if str(listener.listener_id) in self._listeners:
            raise ListenerAlreadyExistsError(
                listener_id=str(listener.listener_id),
            )

        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.LISTENER_ADDED,
                message=f"Added listener: {listener}",
                data=listener.to_json(),
            )
        )
        self._listeners[str(listener.listener_id)] = listener

    @log_and_propagate_error_on_service_method
    def remove_listener_by_listener_id(self, listener_id: str | uuid.UUID) -> None:
        """Removes a listener by its ID.

        Args:
            listener_id (str | uuid.UUID): The ID of the listener to remove.

        Raises:
            ListenerNotFoundError: If the listener does not exist.
            ListenerAlreadyRunningError: If the listener is currently running.
        """
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        if listener.status.state == State.RUNNING:
            raise ListenerAlreadyRunningError(
                listener_str=str(listener),
            )

        removed_listener = self._listeners.pop(str(listener.listener_id))
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.LISTENER_REMOVED,
                message=f"Removed listener: {removed_listener}",
                data=removed_listener.to_json(),
            )
        )
        self._logger.info("Removed listener: {}", removed_listener)
        self._logger.debug("- {!r}", removed_listener)

    @log_and_propagate_error_on_service_method
    def update_listener_by_listener_id(
        self,
        listener_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> BaseListener:
        """Updates a listener's configuration.

        Args:
            listener_id (str | uuid.UUID): The ID of the listener to update.
            name (str | None, optional): The new name for the listener. Defaults to None.
            description (str | None, optional): The new description for the listener. Defaults to None.
            parameters (dict[str, Any] | None, optional): The new parameters for the listener. Defaults to None.

        Returns:
            BaseListener: The updated listener.

        Raises:
            ListenerNotFoundError: If the listener does not exist.
            ListenerAlreadyRunningError: If attempting to update parameters while the listener is running.
            InvalidListenerParameterNameError: If an invalid parameter name is provided.
            InvalidListenerParameterValueError: If an invalid parameter value is provided.
        """
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        # Changed dictionary is used to track what attributes were updated. This data
        # is sent as part of the `LISTENER_UPDATED` event.
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

            # Cannot update running listeners because the parameters change wont be
            # reflected in the listener.
            if listener.status.state == State.RUNNING:
                raise ListenerAlreadyRunningError(
                    listener_str=str(listener),
                )

            # Fill in any missing parameters with values from the existing set of
            # parameters.
            for parameter_name, parameter_value in listener.parameters.items():
                if parameter_name not in parameters:
                    # `parameter_value` could be a list or a dict, so we need to perform
                    # a deep copy to prevent reference sharing.
                    parameters[parameter_name] = copy.deepcopy(parameter_value)

            # Perform validation of `parameters` if they are being updated.
            for parameter_name, parameter_value in parameters.items():
                if parameter_name not in listener.creating_listener_template.options:
                    raise InvalidListenerParameterNameError(
                        listener_str=str(listener),
                        parameter_name=parameter_name,
                    )
                try:
                    listener.creating_listener_template.options[
                        parameter_name
                    ].validate_value(value=parameter_value)
                except OptionValueValidationError as exc:
                    raise InvalidListenerParameterValueError(
                        listener_str=str(listener),
                        parameter_name=parameter_name,
                        parameter_value=str(parameter_value),
                        error_message=str(exc),
                    ) from None
                parameters[parameter_name] = parameter_value

            if parameters == listener.parameters:
                # No parameter changes so skip updating.
                pass
            else:
                # Create a temporary listener whose attributes we copy over to the
                # existing listener. This allows us to perform the `name` and
                # `endpoint` resolution required to update the attribute without
                # inadvertently overwriting any existing state within the existing
                # listener.
                temp_listener = listener.creating_listener_template.create_listener(
                    parameters=parameters,
                )
                listener.name = temp_listener.name
                listener.endpoint = temp_listener.endpoint
                old_parameters = copy.deepcopy(listener.parameters)
                listener.parameters = copy.deepcopy(temp_listener.parameters)
                updated["parameters"] = {
                    "old": old_parameters,  # `old_parameters` is already a deep copy
                    "new": copy.deepcopy(listener.parameters),
                }
                self._logger.info("Updated parameters for listener {}", listener)
                for parameter_name in updated_fields:
                    self._logger.info(
                        "- Updated parameter '{}' from {!r} to {!r}",
                        parameter_name,
                        old_parameters[parameter_name],
                        listener.parameters[parameter_name],
                    )
                self._logger.debug("- {!r}", listener)

        if name is not None and name != listener.name:
            old_name = listener.name
            listener.name = name
            self._logger.info(
                "Updated name for listener {} from '{}' to '{}'",
                listener,
                old_name,
                listener.name,
            )
            self._logger.debug("- {!r}", listener)
            updated["name"] = {
                "old": old_name,
                "new": listener.name,
            }

        if description is not None and description != listener.description:
            old_description = listener.description
            listener.description = description
            self._logger.info(
                "Updated description for listener {} from '{}' to '{}'",
                listener,
                old_description,
                listener.description,
            )
            self._logger.debug(
                "- {!r}",
                listener,
            )
            updated["description"] = {
                "old": old_description,
                "new": description,
            }

        # Only fire events for meaningful changes, skip firing if a no-op update
        # occurred.
        if updated:
            asyncio.create_task(
                self._events_service.trigger_event(
                    event_type=EventType.LISTENER_UPDATED,
                    message=f"Updated listener: {listener}",
                    data={
                        "listener": listener.to_json(),
                        "updated": updated,
                    },
                )
            )
        else:
            self._logger.debug(
                "No updates applied to listener {} as no changes were detected even "
                "though the update method was called",
                listener,
            )

        return listener

    @log_and_propagate_error_on_service_method
    async def start_listener_by_listener_id(
        self, listener_id: str | uuid.UUID, blocking: bool = False
    ) -> BaseListener:
        """Starts a listener by its ID.

        Args:
            listener_id (str | uuid.UUID): The ID of the listener to start.
            blocking (bool, optional): Whether to wait until the listener has fully started. Defaults to False.

        Returns:
            BaseListener: The started listener.

        Raises:
            ListenerNotFoundError: If the listener does not exist.
        """
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        await listener.start()
        if blocking:
            await listener.wait_until_started()

        await self._events_service.trigger_event(
            event_type=EventType.LISTENER_STARTED,
            message=f"Started listener: {listener}",
            data=listener.to_json(),
        )
        self._logger.info("Started listener: {}", listener)
        self._logger.debug("- {!r}", listener)

        return listener

    @log_and_propagate_error_on_service_method
    async def stop_listener_by_listener_id(
        self, listener_id: str | uuid.UUID, blocking: bool = False
    ) -> BaseListener:
        """Stops a listener by its ID.

        Args:
            listener_id (str | uuid.UUID): The ID of the listener to stop.
            blocking (bool, optional): Whether to wait until the listener has fully stopped. Defaults to False.

        Returns:
            BaseListener: The stopped listener.

        Raises:
            ListenerNotFoundError: If the listener does not exist.
        """
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        await listener.stop()
        if blocking:
            await listener.wait_until_stopped()

        await self._events_service.trigger_event(
            event_type=EventType.LISTENER_STOPPED,
            message=f"Stopped listener: {listener}",
            data=listener.to_json(),
        )
        self._logger.info("Stopped listener: {}", listener)
        self._logger.debug("- {!r}", listener)

        return listener

    @log_and_propagate_error_on_service_method
    async def cancel_listener_by_listener_id(
        self, listener_id: str | uuid.UUID, blocking: bool = False
    ) -> BaseListener:
        """Cancels a listener by its ID.

        Args:
            listener_id (str | uuid.UUID): The ID of the listener to cancel.
            blocking (bool, optional): Whether to wait until the listener has fully stopped. Defaults to False.

        Returns:
            BaseListener: The cancelled listener.

        Raises:
            ListenerNotFoundError: If the listener does not exist.
        """
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        await listener.cancel()
        if blocking:
            await listener.wait_until_stopped()

        await self._events_service.trigger_event(
            event_type=EventType.LISTENER_CANCELLED,
            message=f"Cancelled listener: {listener}",
            data=listener.to_json(),
        )
        self._logger.info("Cancelled listener: {}", listener)
        self._logger.debug("- {!r}", listener)

        return listener
