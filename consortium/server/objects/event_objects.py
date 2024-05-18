from enum import StrEnum


class EventType(StrEnum):
    START_SERVER = "START_SERVER"
    STOP_SERVER = "STOP_SERVER"


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

    def to_json(self):
        return {
            "event_type": self.event_type,
            "data": self.data,
        }

    def __str__(self) -> str:
        return str(self.event_type)

    def __repr__(self) -> str:
        return f"Event(event_type={self.event_type!r}, " f"data={self.data!r})"
