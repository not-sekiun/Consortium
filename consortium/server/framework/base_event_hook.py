import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import consortium.server.server_singletons as server_singletons
from consortium.server.objects.event_objects import Event, EventType


class BaseEventHook(ABC):
    def __init__(
        self,
        name: str = "",
        description: str = "",
        authors: list[str] | None = None,
        event_types: list[EventType | str] | None = None,
    ):
        if authors is None:
            authors = []
        if event_types is None:
            event_types = []

        self.event_hook_id = uuid.uuid4()
        self.name = name
        self.description = description
        self.authors = authors
        self.event_types = event_types

        self.environment = SimpleNamespace()
        self.server_services = SimpleNamespace()
        for attr_name, attr_value in server_singletons.__dict__.items():
            # server_singletons also contains a reference to the server which we don't
            # want to set on the plugin.
            if attr_name != "server" and attr_name.endswith("_service"):
                setattr(self.server_services, attr_name, attr_value)
        self.event_hook_project_folder = Path(__file__).parent

    @abstractmethod
    async def run_event_hook(self, event: Event) -> None: ...

    def to_json(self) -> dict[str, Any]:
        return {
            "event_hook_id": str(self.event_hook_id),
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "event_types": [str(event_type) for event_type in self.event_types],
        }

    def __str__(self):
        return f'"{self.name}" ({self.event_hook_id})'

    def __repr__(self):
        return (
            f"BaseEventHook(name={self.name!r}, "
            f"description={self.description!r}, "
            f"authors={self.authors!r}, "
            f"event_types={self.event_types!r})"
        )
