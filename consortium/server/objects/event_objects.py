from enum import StrEnum


class EventType(StrEnum):
    START_SERVER = "START_SERVER"
    STOP_SERVER = "STOP_SERVER"

    LISTENER_CREATED = "LISTENER_CREATED"
    LISTENER_ADDED = "LISTENER_ADDED"
    LISTENER_UPDATED = "LISTENER_UPDATED"
    LISTENER_REMOVED = "LISTENER_REMOVED"
    LISTENER_STARTED = "LISTENER_STARTED"
    LISTENER_STOPPED = "LISTENER_STOPPED"
    LISTENER_CANCELLED = "LISTENER_CANCELLED"

    AGENT_GENERATOR_CREATED = "AGENT_GENERATOR_CREATED"
    AGENT_GENERATOR_ADDED = "AGENT_GENERATOR_ADDED"
    AGENT_GENERATOR_UPDATED = "AGENT_GENERATOR_UPDATED"
    AGENT_GENERATOR_REMOVED = "AGENT_GENERATOR_REMOVED"
    AGENT_GENERATOR_STARTED = "AGENT_GENERATOR_STARTED"
    AGENT_GENERATOR_STOPPED = "AGENT_GENERATOR_STOPPED"
    AGENT_GENERATOR_CANCELLED = "AGENT_GENERATOR_CANCELLED"

    AGENT_UPDATED = "AGENT_UPDATED"
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_DEREGISTERED = "AGENT_DEREGISTERED"
    AGENT_CHECKED_IN = "AGENT_CHECKED_IN"
    AGENT_TASKED = "AGENT_TASKED"

    # TODO: Implement the rest of these events
    LISTENER_RUNTIME_ERRORED = "LISTENER_RUNTIME_ERRORED"

    AGENT_GENERATOR_RUNTIME_ERRORED = "AGENT_GENERATOR_RUNTIME_ERRORED"

    AGENT_RESULT_RECEIVED = "AGENT_RESULT_RECEIVED"

    USER_LOGGED_IN = "USER_LOGGED_IN"
    USER_LOGGED_OUT = "USER_LOGGED_OUT"
    USER_SENT_MESSAGE = "USER_SENT_MESSAGE"


class Event:
    def __init__(
        self,
        event_type: EventType,
        data: dict = None,
    ):
        if data is None:
            data = {}

        self.event_type = event_type
        self.data = data

    def __str__(self) -> str:
        return str(self.event_type)

    def __repr__(self) -> str:
        return f"Event(event_type={self.event_type!r}, " f"data={self.data!r})"

    def to_json(self):
        return {
            "event_type": self.event_type,
            "data": self.data,
        }
