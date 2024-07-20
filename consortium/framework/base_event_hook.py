import sys
import uuid
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Any

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.framework_exceptions.event_hooks_framework_exceptions import (
    EmptyEventHookNameError,
    EventHookConfigurationParameterTypeError,
    RequiredEventHookConfigurationParameterNotDeclaredError,
)
from consortium.server.objects.event_objects import Event, EventType


class BaseEventHook(ABC):
    name: str
    description: str = ""
    authors: set[str] | None = None
    event_types: set[EventType | str] | None = None

    def __init__(self):
        self.event_hook_id = uuid.uuid4()

        self.event_hook_logger = logger.bind(
            logger_name=f"Consortium Event Hook {self}",
        )
        self.environment = SimpleNamespace()
        self.server_services = SimpleNamespace()
        for attr_name, attr_value in server_singletons.__dict__.items():
            # server_singletons also contains a reference to the server which we don't
            # want to set on the plugin.
            if attr_name != "server" and attr_name.endswith("_service"):
                setattr(self.server_services, attr_name, attr_value)

    def __init_subclass__(cls, **kwargs):
        if cls.authors is None:
            cls.authors = set()
        if cls.event_types is None:
            cls.event_types = set()

        if not hasattr(cls, "name"):
            # The event hook is identified by its name, but at this point we are
            # still validating the name parameter, so we refer to it by its filepath
            # for now.
            raise RequiredEventHookConfigurationParameterNotDeclaredError(
                event_hook=sys.modules[cls.__module__].__file__,
                parameter_name="name",
            )
        if not isinstance(cls.name, str):
            raise EventHookConfigurationParameterTypeError(
                event_hook=sys.modules[cls.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not cls.name:
            raise EmptyEventHookNameError(
                event_hook_filepath=sys.modules[cls.__module__].__file__,
            )
        # From here onwards we can refer to event hook by its name.
        if not isinstance(cls.description, str):
            raise EventHookConfigurationParameterTypeError(
                event_hook=cls.name,
                parameter_name="description",
                parameter_type="str",
            )
        if not isinstance(cls.authors, set):
            raise EventHookConfigurationParameterTypeError(
                event_hook=cls.name,
                parameter_name="authors",
                parameter_type="set",
            )
        for author in cls.authors:
            if not isinstance(author, str):
                raise EventHookConfigurationParameterTypeError(
                    event_hook=cls.name,
                    error_message=(
                        "The elements in the authors set must be strings for event "
                        f"hook '{cls.name}'."
                    ),
                )
        if not isinstance(cls.event_types, set):
            raise EventHookConfigurationParameterTypeError(
                event_hook=cls.name,
                parameter_name="event_types",
                parameter_type="set",
            )
        for event_type in cls.event_types:
            if not isinstance(event_type, (EventType, str)):
                raise EventHookConfigurationParameterTypeError(
                    event_hook=cls.name,
                    error_message=(
                        "The elements in the event types set must be event type "
                        f"objects for event hook '{cls.name}'."
                    ),
                )

        super().__init_subclass__(**kwargs)

    def __str__(self):
        return f"{self.name} ({self.event_hook_id})"

    def __repr__(self):
        return (
            f"BaseEventHook(name={self.name!r}, "
            f"description={self.description!r}, "
            f"authors={self.authors!r}, "
            f"event_types={self.event_types!r})"
        )

    @abstractmethod
    async def on_event_hook_triggered(self, event: Event) -> None: ...

    def to_json(self) -> dict[str, Any]:
        return {
            "event_hook_id": str(self.event_hook_id),
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "event_types": [str(event_type) for event_type in self.event_types],
        }
