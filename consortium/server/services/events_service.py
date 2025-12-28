from collections.abc import Callable, Coroutine
from typing import Any

from loguru import logger

from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.framework.framework_types import JSON
from consortium.server.exceptions.consortium_exceptions.events_consortium_exceptions import (
    EventHandlerAlreadyRegisteredError,
    EventHandlerNotRegisteredError,
)
from consortium.server.server_logging import LoggerType
from consortium.server.utils import log_and_propagate_error_on_service_method


# TODO: Support creating custom events. <- get a load of this guy i dont know about that lol
class EventsService:
    def __init__(self):
        self._event_handlers = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)
        self._custom_event_types = set()

    def __str__(self):
        return "Events Service"

    def __repr__(self):
        return "EventsService()"

    @log_and_propagate_error_on_service_method
    def register_event_handler_to_event_type(
        self,
        event_type: EventType,
        event_handler: Callable[[Event], Coroutine[Any, Any, None]],
    ) -> None:
        if str(event_type) in self._event_handlers:
            if event_handler in self._event_handlers[str(event_type)]:
                raise EventHandlerAlreadyRegisteredError
            self._event_handlers[str(event_type)].append(event_handler)
        else:
            self._event_handlers[str(event_type)] = [event_handler]

    @log_and_propagate_error_on_service_method
    def deregister_event_handler_from_event_type(
        self,
        event_type: EventType,
        event_handler: Callable[[Event], Coroutine[None, None, None]],
    ) -> None:
        try:
            event_handlers = self._event_handlers[str(event_type)]
        except KeyError:
            raise EventHandlerNotRegisteredError from None

        try:
            # `event_handlers` is passed by reference here.
            event_handlers.remove(event_handler)
        except ValueError:
            raise EventHandlerNotRegisteredError from None

    @log_and_propagate_error_on_service_method
    def get_registered_event_handlers_from_event_type(
        self,
        event_type: EventType,
    ) -> list[Callable[[EventType], Coroutine[None, None, None]]]:
        try:
            return self._event_handlers[event_type]
        except KeyError:
            # KeyError being raised implies that no event handlers was registered, so
            # we return an empty list.
            return []

    @log_and_propagate_error_on_service_method
    def get_event_types_from_registered_event_handler(
        self,
        event_handler: Callable[[Event], Coroutine[Any, Any, None]],
    ) -> list[EventType]:
        handled_events = []
        for event_type, handlers in self._event_handlers.items():
            if event_handler in handlers:
                handled_events.append(EventType(event_type))
        return handled_events

    @log_and_propagate_error_on_service_method
    def get_all_event_types(self) -> list[str]:
        return list(EventType)

    @log_and_propagate_error_on_service_method
    # async def trigger_event(self, event: Event):
    async def trigger_event(
        self, event_type: EventType, message: str = "", data: JSON | None = None
    ) -> None:
        if str(event_type) not in self._event_handlers:
            return
        if data is None:
            data = {}

        event = Event(
            event_type=event_type,
            message=message,
            data=data,
        )
        for event_handler in self._event_handlers[str(event.event_type)]:
            try:
                await event_handler(event)
            except Exception as exc:
                self._logger.error(
                    "Unhandled exception occurred while triggering event handler. "
                    "{}: {}",
                    exc.__class__.__name__,
                    exc,
                )
