from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)
from consortium.server.objects.event_objects import EventType


class EventsServiceError(BaseServiceException):
    pass


class EventHandlerAlreadyRegisteredError(EventsServiceError):
    def __init__(self, event_type: EventType):
        super().__init__(
            message=(
                f"Failed to register the provided event handler for event "
                f"{event_type}. The provided event handler is already registered for "
                f"that event."
            ),
        )


class EventHandlerNotRegisteredError(EventsServiceError):
    def __init__(self, event_type: EventType):
        super().__init__(
            message=(
                f"Failed to deregister the requested event handler for event "
                f"{event_type}. The requested event handler is not registered for "
                f"that event."
            ),
        )
