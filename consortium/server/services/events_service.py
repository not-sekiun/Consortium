from typing import Any, Callable, Coroutine

from loguru import logger

from consortium.framework.event_hooks.event import Event, EventType
from consortium.server.exceptions.service_exceptions.events_service_exceptions import (
    EventHandlerAlreadyRegisteredError,
    EventHandlerNotRegisteredError,
)


# TODO: Support creating custom events.
class EventsService:
    def __init__(self):
        self._event_handlers = {}
        self.events_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.events_service_logger.debug(f"Started {self}")
        self._custom_event_types = set()

    def __str__(self):
        return "Events Service"

    def __repr__(self):
        return "EventsService()"

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

    def deregister_event_handler_from_event_type(
        self,
        event_type: EventType,
        event_handler: Callable[[Event], Coroutine[None, None, None]],
    ) -> None:
        try:
            event_handlers = self._event_handlers[str(event_type)]
        except KeyError:
            raise EventHandlerNotRegisteredError

        try:
            # `event_handlers` is passed by reference here.
            event_handlers.remove(event_handler)
        except ValueError:
            raise EventHandlerNotRegisteredError

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

    def get_event_types_from_registered_event_handler(
        self,
        event_handler: Callable[[Event], Coroutine[Any, Any, None]],
    ) -> list[EventType]:
        handled_events = []
        for event_type, handlers in self._event_handlers.items():
            if event_handler in handlers:
                handled_events.append(EventType(event_type))
        return handled_events

    @staticmethod
    def get_all_event_types() -> list[str]:
        return list(EventType)

    async def trigger_event(self, event: Event):
        if str(event.event_type) not in self._event_handlers:
            return

        for event_handler in self._event_handlers[str(event.event_type)]:
            try:
                await event_handler(event)
            except Exception as exc:
                self.events_service_logger.error(
                    "Fatal error occurred while triggering event handler: {}",
                    exc,
                )
