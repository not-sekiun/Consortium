"""Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`EventsError`][consortium.server.exceptions.consortium_exceptions.events_consortium_exceptions.EventsError]
        - [`EventsServiceError`][consortium.server.exceptions.consortium_exceptions.events_consortium_exceptions.EventsServiceError]
            - [`EventHandlerAlreadyRegisteredError`][consortium.server.exceptions.consortium_exceptions.events_consortium_exceptions.EventHandlerAlreadyRegisteredError]
            - [`EventHandlerNotRegisteredError`][consortium.server.exceptions.consortium_exceptions.events_consortium_exceptions.EventHandlerNotRegisteredError]
"""

from consortium.framework.event_hooks import EventType
from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class EventsError(BaseConsortiumError):
    """Base exception for all events-related errors."""

    code = "EVENTS_ERROR"


class EventsServiceError(EventsError):
    """Base exception for all errors that occur within the events service."""

    code = "EVENTS_SERVICE_ERROR"


class EventHandlerAlreadyRegisteredError(EventsServiceError):
    """Raised when the provided event handler is already registered for the specified
    event type in the events service.
    """

    code = "EVENT_HANDLER_ALREADY_REGISTERED_ERROR"

    def __init__(self, event_type: EventType):
        super().__init__(
            message=(
                f"Failed to register the provided event handler for event "
                f"{event_type}. The provided event handler is already registered for "
                f"that event."
            ),
        )


class EventHandlerNotRegisteredError(EventsServiceError):
    """Raised when the requested event handler is not registered for the specified event
    type in the events service.
    """

    code = "EVENT_HANDLER_NOT_REGISTERED_ERROR"

    def __init__(self, event_type: EventType):
        super().__init__(
            message=(
                f"Failed to deregister the requested event handler for event "
                f"{event_type}. The requested event handler is not registered for "
                f"that event."
            ),
        )
