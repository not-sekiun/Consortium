from enum import StrEnum


class EventType(StrEnum):
    START_SERVER = "START_SERVER"
    STOP_SERVER = "STOP_SERVER"

    # TODO: Implement the rest of these events
    LISTENER_CREATED = "LISTENER_CREATED"
    LISTENER_STARTED = "LISTENER_STARTED"
    LISTENER_STOPPED = "LISTENER_STOPPED"
    LISTENER_RUNTIME_ERRORED = "LISTENER_RUNTIME_ERRORED"
    LISTENER_DELETED = "LISTENER_DELETED"

    AGENT_GENERATOR_CREATED = "AGENT_GENERATOR_CREATED"
    AGENT_GENERATOR_STARTED = "AGENT_GENERATOR_STARTED"
    AGENT_GENERATOR_STOPPED = "AGENT_GENERATOR_STOPPED"
    AGENT_GENERATOR_RUNTIME_ERRORED = "AGENT_GENERATOR_RUNTIME_ERRORED"
    AGENT_GENERATOR_DELETED = "AGENT_GENERATOR_DELETED"

    AGENT_CONNECTED = "AGENT_CREATED"
    AGENT_DISCONNECTED = "AGENT_DELETED"
    AGENT_CHECKED_IN = "AGENT_CHECKED_IN"


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
