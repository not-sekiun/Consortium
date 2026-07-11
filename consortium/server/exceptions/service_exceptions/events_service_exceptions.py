"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`EventsServiceError`][consortium.server.exceptions.service_exceptions.events_service_exceptions.EventsServiceError]
        - [`EventHandlerAlreadyRegisteredError`][consortium.server.exceptions.service_exceptions.events_service_exceptions.EventHandlerAlreadyRegisteredError]
        - [`EventHandlerNotRegisteredError`][consortium.server.exceptions.service_exceptions.events_service_exceptions.EventHandlerNotRegisteredError]
"""

from consortium.framework.event_hooks import EventType
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class EventsServiceError(BaseServiceError):
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
