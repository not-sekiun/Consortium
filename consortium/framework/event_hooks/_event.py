from consortium.framework.event_hooks.event_type import EventType


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
        return f"Event(event_type={self.event_type!r}, data={self.data!r})"

    def to_json(self):
        return {
            "event_type": self.event_type,
            "data": self.data,
        }
