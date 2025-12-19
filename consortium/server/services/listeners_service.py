import copy
import uuid
from typing import Any

from loguru import logger

# from consortium.framework.listeners._listener_status import ListenerState
from consortium.framework._components._component_status import State
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.framework.listeners.base_listener import BaseListener
from consortium.server.exceptions.framework_exceptions import (
    listeners_framework_exceptions as framework_excs,
)
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.service_exceptions import (
    listeners_service_exceptions as svc_excs,
)
from consortium.server.server_logging import LoggerType
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
    def get_listener_by_listener_id(self, listener_id: str | uuid.UUID) -> BaseListener:
        listener_id = normalize_uuid(listener_id)

        try:
            listener = self._listeners[listener_id]
        except KeyError:
            raise svc_excs.ListenerNotFoundError(listener_id=listener_id) from None
        self._logger.debug("Retrieved listener: {!r}", listener)
        return listener

    @log_and_propagate_error_on_service_method
    def get_all_listeners(self) -> list[BaseListener]:
        all_listeners = list(self._listeners.values())
        self._logger.debug(
            "Retrieved all listeners ({} retrieved)",
            len(all_listeners),
        )
        return all_listeners

    @log_and_propagate_error_on_service_method
    async def create_listener_from_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
        parameters: dict[str, Any],
        name: str | None = None,
        description: str = "",
    ) -> BaseListener:
        listener_template = self._listener_templates_service.get_listener_template_by_listener_template_id(
            listener_template_id=listener_template_id,
        )

        listener = listener_template.create_listener(
            name=name,
            description=description,
            parameters=parameters,
        )
        self._listeners[str(listener.listener_id)] = listener
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_CREATED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._logger.info("Created listener: {}", listener)
        self._logger.debug("- {!r}", listener)

        return listener

    @log_and_propagate_error_on_service_method
    async def add_listener(self, listener: BaseListener) -> None:
        if str(listener.listener_id) in self._listeners:
            raise svc_excs.ListenerAlreadyExistsError

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_ADDED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._listeners[str(listener.listener_id)] = listener

    @log_and_propagate_error_on_service_method
    async def remove_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        if listener.status.state == State.RUNNING:
            raise framework_excs.ListenerAlreadyRunningError

        removed_listener = self._listeners.pop(listener_id)
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_REMOVED,
                data={"listener_id": str(removed_listener.listener_id)},
            ),
        )
        self._logger.info("Removed listener: {}", removed_listener)
        self._logger.debug("- {!r}", removed_listener)

    @log_and_propagate_error_on_service_method
    async def update_listener_by_listener_id(
        self,
        listener_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ):
        listener_id = str(listener_id)
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
                raise framework_excs.ListenerAlreadyRunningError

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
                    raise svc_excs.InvalidListenerParameterNameError(
                        listener=str(listener),
                        parameter_name=parameter_name,
                    )
                try:
                    listener.creating_listener_template.options[
                        parameter_name
                    ].validate_value(value=parameter_value)
                except OptionValueValidationError as exc:
                    raise svc_excs.InvalidListenerParameterValueError(
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
                self._logger.info("Updated parameters for listener {}.", listener)
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
                "Updated name for listener {} from '{}' to '{}'.",
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
                "Updated description for listener {} from '{}' to '{}'.",
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
            await self._events_service.trigger_event(
                event=Event(
                    event_type=EventType.LISTENER_UPDATED,
                    data={
                        "listener_id": str(listener.listener_id),
                        "updated": updated,
                    },
                ),
            )
        else:
            self._logger.debug(
                "No updates applied to listener {} as no changes were detected even "
                "though the update method was called.",
                listener,
            )

        return listener

    @log_and_propagate_error_on_service_method
    async def start_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        await listener.start()
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_STARTED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._logger.info("Started listener: {}", listener)
        self._logger.debug("- {!r}", listener)

    @log_and_propagate_error_on_service_method
    async def stop_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        await listener.stop()
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_STOPPED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._logger.info("Stopped listener: {}", listener)
        self._logger.debug("- {!r}", listener)

    @log_and_propagate_error_on_service_method
    async def cancel_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        await listener.cancel()
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_CANCELLED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._logger.info("Cancelled listener: {}", listener)
        self._logger.debug("- {!r}", listener)
