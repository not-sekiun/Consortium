from collections.abc import Callable, Coroutine
from typing import Any

from loguru import logger

from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.framework.framework_types import JSON
from consortium.framework.signal_exceptions import (
    event_hooks_signal_exceptions as event_hook_framework_excs,
)
from consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions import (
    EventHookTriggerError,
)
from consortium.server.exceptions.service_exceptions.events_service_exceptions import (
    EventHandlerAlreadyRegisteredError,
    EventHandlerNotRegisteredError,
    InvalidEventTypeError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import log_and_propagate_error_on_service_method


# TODO: Support creating custom events. <- get a load of this guy i dont know about that lol
class EventsService:
    def __init__(self):
        self._event_handlers = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

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
        """Registers an async event handler for the specified event type.

        Args:
            event_type: The event type to subscribe the handler to.
            event_handler: An async callable that accepts an `Event` and is invoked
                whenever the event type is triggered.

        Raises:
            InvalidEventTypeError: If the provided event type does not correspond to a
                valid `EventType` member.
            EventHandlerAlreadyRegisteredError: If the same handler is already
                registered for the given event type.
        """
        try:
            EventType(event_type)
        except ValueError:
            raise InvalidEventTypeError(event_type) from None

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
        """Removes a previously registered event handler from the specified event type.

        Args:
            event_type: The event type to unsubscribe the handler from.
            event_handler: The async callable to remove.

        Raises:
            EventHandlerNotRegisteredError: If the handler is not currently registered
                for the given event type.
        """
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
        """Returns all handlers currently registered for the specified event type.

        Args:
            event_type: The event type whose handlers to retrieve.

        Returns:
            A list of registered handlers. Empty if no handlers are registered for the
            event type.
        """
        try:
            return self._event_handlers[str(event_type)]
        except KeyError:
            # KeyError being raised implies that no event handlers was registered, so
            # we return an empty list.
            return []

    @log_and_propagate_error_on_service_method
    def get_event_types_from_registered_event_handler(
        self,
        event_handler: Callable[[Event], Coroutine[Any, Any, None]],
    ) -> list[EventType]:
        """Returns all event types that the given handler is currently registered for.

        Args:
            event_handler: The handler to look up.

        Returns:
            A list of event types the handler is subscribed to. Empty if the handler is
            not registered for any event type.
        """
        handled_events = []
        for event_type, handlers in self._event_handlers.items():
            if event_handler in handlers:
                handled_events.append(EventType(event_type))
        return handled_events

    @log_and_propagate_error_on_service_method
    def get_all_event_types(self) -> list[str]:
        """Returns all supported event types.

        Returns:
            A list of all values from the `EventType` enum.
        """
        return list(EventType)

    @log_and_propagate_error_on_service_method
    async def trigger_event(
        self, event_type: EventType, message: str = "", data: JSON | None = None
    ) -> None:
        """Triggers an event, invoking all handlers registered for the given event type.

        Handlers are called sequentially. If any handler raises an exception, remaining
        handlers still run, and all exceptions are collected and re-raised together as
        an `ExceptionGroup`. Event hooks that raise `EventHookTriggerError` (the
        framework-level signal from
        `consortium.framework.signal_exceptions.event_hooks_signal_exceptions`) from
        `on_triggered()` have that error remapped to the consortium-level
        `EventHookTriggerError` before being collected, preserving the original
        `message` and `detail`.

        Args:
            event_type: The type of event to trigger.
            message: A human-readable description of the event.
            data: Structured data payload associated with the event. Defaults to an
                empty dict when `None`.

        Raises:
            ExceptionGroup: If one or more event handlers raise exceptions. The group
                can contain the consortium-level `EventHookTriggerError` (remapped from
                the framework-level signal raised by a handler's `on_triggered()`)
                alongside any other exception a handler raised.
        """
        if str(event_type) not in self._event_handlers:
            return
        if data is None:
            data = {}

        errors = []
        event = Event(
            event_type=event_type,
            message=message,
            data=data,
        )
        for event_handler in self._event_handlers[str(event.event_type)]:
            try:
                await event_handler(event)
            except event_hook_framework_excs.EventHookTriggerError as exc:
                errors.append(
                    EventHookTriggerError(
                        event_hook_str=str(
                            getattr(event_handler, "__self__", event_handler)
                        ),
                        error_message=exc.message,
                        detail=exc.detail,
                    )
                )
            except Exception as exc:
                errors.append(exc)

        if errors:
            raise ExceptionGroup(
                f"{len(errors)} event handler(s) failed for {event.event_type!r}",
                errors,
            )
