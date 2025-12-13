import copy
from typing import Any

from loguru import logger

# from consortium.framework.listeners._listener_status import ListenerState
from consortium.framework._components._component_status import State
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.framework.listeners.base_listener import BaseListener
from consortium.framework.options.exceptions import OptionValueValidationError
from consortium.server.exceptions.framework_exceptions import (
    listener_templates_framework_exceptions as listener_templates_framework_excs,
    listeners_framework_exceptions as listeners_framework_excs,
)
from consortium.server.exceptions.service_exceptions import (
    listeners_service_exceptions as listeners_service_excs,
)
from consortium.server.server_logging import LoggerType
from consortium.server.services.events_service import EventsService
from consortium.server.services.listener_templates_service import (
    ListenerTemplatesService,
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

    def get_listener_by_listener_id(self, listener_id: str) -> BaseListener:
        try:
            listener = self._listeners[listener_id]
        except KeyError:
            raise listeners_service_excs.ListenerNotFoundError(
                listener_id=listener_id
            ) from None

        self._logger.debug("Retrieved listener: {!r}", listener)
        return listener

    def get_all_listeners(self) -> list[BaseListener]:
        all_listeners = list(self._listeners.values())
        self._logger.debug(
            "Retrieved all listeners ({} retrieved)",
            len(all_listeners),
        )
        return all_listeners

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
        try:
            listener = listener_template.create_listener(
                name=name,
                description=description,
                parameters=parameters,
            )
        except (
            listener_templates_framework_excs.ListenerTemplateOptionNotFoundError
        ) as exc:
            raise listeners_service_excs.ListenerTemplateOptionNotFoundError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except (
            listener_templates_framework_excs.ListenerTemplateOptionValueValidationError
        ) as exc:
            raise listeners_service_excs.ListenerTemplateOptionValueValidationError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except (
            listener_templates_framework_excs.MissingRequiredListenerTemplateOptionError
        ) as exc:
            raise listeners_service_excs.MissingRequiredListenerTemplateOptionError(
                message=exc.message,
                detail=exc.detail,
            ) from None

        self._listeners[str(listener.listener_id)] = listener
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_CREATED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._logger.info("Created listener: {}", listener)
        self._logger.debug("Created listener: {!r}", listener)
        return listener

    async def add_listener(self, listener: BaseListener) -> None:
        if str(listener.listener_id) in self._listeners:
            raise listeners_service_excs.ListenerAlreadyExistsError
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_ADDED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._listeners[str(listener.listener_id)] = listener

    async def remove_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        if listener.status.state == State.RUNNING:
            raise listeners_service_excs.ListenerAlreadyRunningError

        removed_listener = self._listeners.pop(listener_id)
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_REMOVED,
                data={"listener_id": str(removed_listener.listener_id)},
            ),
        )
        self._logger.info("Removed listener: {}", removed_listener)
        self._logger.debug("Removed listener: {!r}", removed_listener)

    async def update_listener_name_by_listener_id(
        self,
        listener_id: str,
        name: str,
    ) -> BaseListener:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        old_name = listener.name
        listener.name = name
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_UPDATED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._logger.info(
            "Updated name for listener {} from '{}' to '{}'.",
            listener,
            old_name,
            name,
        )
        self._logger.debug(
            "Updated name for listener {!r} from '{}' to '{}'.",
            listener,
            old_name,
            name,
        )
        return listener

    async def update_listener_description_by_listener_id(
        self,
        listener_id: str,
        description: str,
    ) -> BaseListener:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        old_description = listener.description
        listener.description = description
        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_UPDATED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._logger.info(
            "Updated description for listener {} from '{}' to '{}'.",
            listener,
            old_description,
            description,
        )
        self._logger.debug(
            "Updated description for listener {!r} from '{}' to '{}'.",
            listener,
            old_description,
            description,
        )
        return listener

    async def update_listener_parameters_by_listener_id(
        self,
        listener_id: str,
        parameters: dict[str, Any],
    ) -> BaseListener:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        if listener.status.state == State.RUNNING:
            raise listeners_service_excs.ListenerAlreadyRunningError

        for parameter_name, parameter_value in listener.parameters.items():
            if parameter_name not in parameters:
                # `parameter_value` could be a list or a dict, so we need to perform
                # a deep copy to prevent reference sharing.
                parameters[parameter_name] = copy.deepcopy(parameter_value)

        for parameter_name, parameter_value in parameters.items():
            if parameter_name not in listener.creating_listener_template.options:
                raise listeners_service_excs.InvalidListenerParameterNameError(
                    listener=str(listener),
                    parameter_name=parameter_name,
                )
            try:
                listener.creating_listener_template.options[
                    parameter_name
                ].validate_value(value=parameter_value)
            except OptionValueValidationError as exc:
                raise listeners_service_excs.InvalidListenerParameterValueError(
                    listener_str=str(listener),
                    parameter_name=parameter_name,
                    parameter_value=str(parameter_value),
                    error_message=str(exc),
                ) from None
            parameters[parameter_name] = parameter_value

        # Create a temporary listener whose attributes we copy over to the
        # existing listener. This allows us to perform the name and
        # endpoint resolution required to update the attribute without
        # inadvertently overwriting any existing state within the existing
        # listener.
        temporary_listener = listener.creating_listener_template.create_listener(
            parameters=parameters,
        )
        listener.name = temporary_listener.name
        listener.endpoint = temporary_listener.endpoint
        listener.parameters = copy.deepcopy(temporary_listener.parameters)

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_UPDATED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
        self._logger.info(
            "Updated parameters for listeners {} to {}",
            listener,
            parameters,
        )
        self._logger.debug(
            "Updated parameters for listeners {!r} to {}",
            listener,
            parameters,
        )
        return listener

    async def start_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        try:
            await listener.start()
        except listeners_framework_excs.ListenerStartError as exc:
            raise listeners_service_excs.ListenerStartError(
                message=str(exc),
                detail=exc.detail,
            ) from None
        except listeners_framework_excs.ListenerAlreadyRunningError as exc:
            raise listeners_service_excs.ListenerAlreadyRunningError(
                message=exc.message
            ) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_STARTED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )

    async def stop_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        try:
            await listener.stop()
        except listeners_framework_excs.ListenerStopError as exc:
            raise listeners_service_excs.ListenerStopError(
                message=str(exc),
                detail=exc.detail,
            ) from None
        except listeners_framework_excs.ListenerNotRunningError as exc:
            raise listeners_service_excs.ListenerNotRunningError(
                message=exc.message
            ) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_STOPPED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )

    async def cancel_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        try:
            await listener.cancel()
        except listeners_framework_excs.ListenerNotRunningError as exc:
            raise listeners_service_excs.ListenerNotRunningError(
                message=exc.message
            ) from None

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.LISTENER_CANCELLED,
                data={"listener_id": str(listener.listener_id)},
            ),
        )
