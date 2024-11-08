import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.framework.event_hooks.event import Event, EventType
from consortium.server.exceptions.framework_exceptions.event_hooks_framework_exceptions import (
    EmptyEventHookNameError,
    EventHookConfigurationParameterTypeError,
    RequiredEventHookConfigurationParameterNotDeclaredError,
)


class BaseEventHook:
    """
    Base class for event hooks. Event hooks are used to trigger custom actions based on
    events that occur in the system.

    To create custom event hooks, subclass this class and implement the
    `on_event_hook_triggered` method. The `on_event_hook_triggered` method is called
    when the event hook is triggered by the specified event that it is subscribed to.
    The event hook can then perform any necessary actions based on the event data.

    Attributes:
        event_hook_id (uuid.UUID):
            The unique primary identifier for the event hook. The event hook ID is an
            object that represents a version 4 UUID string.
        name (str):
            The name of the event hook. The name does not have to be unique as it does
            not serve as the primary identifier of the event hook.
        description (str):
            A description of the event hook.
        authors (set[str]):
            The authors of the event hook.
        event_types (set[EventType | str]):
            The event types that the event hook is subscribed to.
        event_hook_logger (loguru.logger):
            A loguru `Logger` object that can be used by the event hook to log messages
            to the framework's logging system. The logger is identified in the log messages
            with the event hook's name and event hook ID.
        environment (types.SimpleNamespace):
            A namespace object that allows the listener to store any variables that it
            wants without potentially conflicting with other variables in the event
            hook. This is primarily used for saving state date between different
            invocations of the event hook across multiple events.
        event_hook_project_folder (pathlib.Path):
            The path to the event hook's project folder. This is the folder that
            contains the event hook's source code. This is primarily used for loading
            any custom configuration files or resources that the event hook needs to
            function.
    """

    name: str
    description: str = ""
    authors: set[str] | None = None
    event_types: set[EventType | str] | None = None

    def __init__(self):
        self.event_hook_id = uuid.uuid4()
        self.event_hook_logger = logger.bind(
            logger_name=f"Event Hook {self}",
        )
        self.environment = SimpleNamespace()
        # Dynamically construct the `server_services` simple namespace object by
        # iterating over the attributes of the `server_singletons` module and adding
        # any object with an attribute that ends with `_service`.
        services_dict = {}
        for attr in dir(server_singletons):
            if attr.endswith("_service"):
                services_dict[attr] = getattr(server_singletons, attr)
        self.server_services = SimpleNamespace(**services_dict)
        self.event_hook_project_folder = Path(__file__).parent

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
        return f"'{self.name}' ({self.event_hook_id})"

    def __repr__(self):
        return (
            f"BaseEventHook(name={self.name!r}, "
            f"description={self.description!r}, "
            f"authors={self.authors!r}, "
            f"event_types={self.event_types!r})"
        )

    async def on_event_hook_triggered(self, event: Event) -> None: ...

    def to_json(self) -> dict[str, Any]:
        return {
            "event_hook_id": str(self.event_hook_id),
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "event_types": [str(event_type) for event_type in self.event_types],
        }
