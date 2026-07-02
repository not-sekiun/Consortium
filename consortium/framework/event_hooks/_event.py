from pydantic import JsonValue

from consortium.framework.event_hooks.event_type import EventType


class Event:
    def __init__(
        self,
        event_type: EventType,
        message: str = "",
        data: dict[str, JsonValue] | None = None,
    ):
        self.event_type = event_type
        self.message = message
        self.data = data if data is not None else {}

    def __str__(self) -> str:
        return str(self.event_type)

    def __repr__(self) -> str:
        return (
            f"Event("
            f"event_type={self.event_type!r}, "
            f"message={self.message!r}, "
            f"data={self.data!r}"
            f")"
        )

    def to_json(self):
        return {
            "event_type": str(self.event_type),
            "message": self.message,
            "data": self.data,
        }
