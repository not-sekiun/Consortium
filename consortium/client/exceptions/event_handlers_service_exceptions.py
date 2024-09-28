class InvalidEventTypeError(Exception):
    def __init__(self, event_type: str):
        super().__init__(
            "Failed to perform the requested operation. Invalid event type "
            f"'{event_type}' was provided.",
        )


class EventHandlerNotRegisteredError(Exception):
    def __init__(self, event_type: str):
        super().__init__(
            "Failed to deregister the provided event handler. The provided event "
            f"handler was not registered for event type '{event_type}'.",
        )


class EventHandlerAlreadyRegisteredError(Exception):
    def __init__(self, event_type: str):
        super().__init__(
            "Failed to register the provided event handler. The provided event handler "
            f"was already registered for event type '{event_type}'.",
        )
