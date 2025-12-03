import pathlib
import sys
import types
import uuid
from typing import Any

from loguru import logger

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
import consortium.server.server_singletons as server_singletons
from consortium.framework._components import ComponentMetadata, ComponentModel
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.framework_exceptions.event_hooks_framework_exceptions import (
    EmptyEventHookLabelError,
    InvalidEventHookConfigurationParameterTypeError,
    InvalidEventHookDependencyVersionSpecifierError,
    InvalidEventHookVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingEventHookConfigurationParameterError,
)
from consortium.server.utils.data_structure_utils import remap_exception


class _EventHookModel(ComponentModel):
    event_types: set[EventType] | None = None


class BaseEventHook(ComponentMetadata):
    # """
    # Base class for event hooks. Event hooks are used to trigger custom actions based on
    # events that occur in the system.
    #
    # To create custom event hooks, subclass this class and implement the
    # `on_event_hook_triggered` method. The `on_event_hook_triggered` method is called
    # when the event hook is triggered by the specified event that it is subscribed to.
    # The event hook can then perform any necessary actions based on the event data.
    #
    # Attributes:
    #     event_hook_id (uuid.UUID):
    #         The unique primary identifier for the event hook. The event hook ID is an
    #         object that represents a version 4 UUID string.
    #     name (str):
    #         The name of the event hook. The name does not have to be unique as it does
    #         not serve as the primary identifier of the event hook.
    #     description (str):
    #         A description of the event hook.
    #     authors (set[str]):
    #         The authors of the event hook.
    #     event_hook_version:
    #         The version of the event hook. This version is a `packaging.version.Version`
    #         object that represents a version string. The version string must be a valid
    #         version string according to the `PEP 440` specification.
    #     compatible_framework_version:
    #         A specifier string that specifies the compatible framework version for the
    #         plugin. The specifier string must be a valid specifier string according to
    #         the `PEP 440` specification.
    #     event_types (set[EventType | str]):
    #         The event types that the event hook is subscribed to.
    #     event_hook_logger (loguru.logger):
    #         A loguru `Logger` object that can be used by the event hook to log messages
    #         to the framework's logging system. The logger is identified in the log
    #         messages with the event hook's name and event hook ID.
    #     environment (types.SimpleNamespace):
    #         A namespace object that allows the listener to store any variables that it
    #         wants without potentially conflicting with other variables in the event
    #         hook. This is primarily used for saving state date between different
    #         invocations of the event hook across multiple events.
    #     server_services (types.SimpleNamespace):
    #         A namespace object that contains all the Consortium server services that
    #         allow for programmatic access to the different framework components.
    #     event_hook_project_folder (pathlib.Path):
    #         The path to the event hook's project folder. This is the folder that
    #         contains the event hook's source code. This is primarily used for loading
    #         any custom configuration files or resources that the event hook needs to
    #         function.
    #     third_party_dependencies:
    #         The set of third-party library dependencies that this plugin depends on.
    #         This plugin will not load if the plugin service cannot import these
    #         third-party libraries. The format of each dependency string is specified by
    #         `PEP 440` specification.
    # """

    _METADATA_MODEL = _EventHookModel
    _EXCEPTION_MAP = {
        comp_excs.MissingComponentConfigurationParameterError: MissingEventHookConfigurationParameterError,
        comp_excs.EmptyComponentLabelError: EmptyEventHookLabelError,
        comp_excs.InvalidComponentVersionError: InvalidEventHookVersionError,
        comp_excs.InvalidFrameworkVersionSpecifierError: InvalidFrameworkVersionSpecifierError,
        comp_excs.InvalidComponentDependencyVersionSpecifierError: InvalidEventHookDependencyVersionSpecifierError,
        comp_excs.InvalidComponentConfigurationParameterTypeError: InvalidEventHookConfigurationParameterTypeError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_str": "event_hook_str",
        "component_filepath": "event_hook_filepath",
    }

    event_types: set[EventType] | None = None

    def __init__(self):
        self.event_hook_id = uuid.uuid4()
        self.logger = logger.bind(
            logger_name=f"Event Hook - {self}",
        )
        self.environment = types.SimpleNamespace()
        # Dynamically construct the `server_services` simple namespace object by
        # iterating over the attributes of the `server_singletons` module and adding
        # any object with an attribute that ends with `_service`.
        services_dict = {}
        for attr in dir(server_singletons):
            if attr.endswith("_service"):
                services_dict[attr] = getattr(server_singletons, attr)
        self.server_services = types.SimpleNamespace(**services_dict)
        self.event_hook_project_folder = pathlib.Path(
            sys.modules[self.__module__].__file__,
        ).parents[0]
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        cls.event_types = cls.event_types or set()
        try:
            cls._validate_metadata()
        except comp_excs.ComponentsFrameworkError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.exc_kwargs,
                exception_map=cls._EXCEPTION_MAP,
                exception_kwargs_map=cls._EXCEPTION_KWARGS_MAP,
            ) from None
        super().__init_subclass__(**kwargs)

    def __str__(self):
        return f"{self.name} ({str(self.event_hook_id)})"

    def __repr__(self):
        return (
            f"EventHook("
            f"event_hook_id={self.event_hook_id!r}, "
            f"label={self.label!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"version={self.version!r}, "
            f"compatible_framework_version={self.compatible_framework_version!r}, "
            f"authors={self.authors!r}, "
            f"component_dependencies={self.component_dependencies!r}, "
            f"third_party_dependencies={self.third_party_dependencies!r}, "
            f"event_types={self.event_types!r}"
            f")"
        )

    async def on_event_hook_setup(self) -> None: ...

    async def on_event_hook_triggered(self, event: Event) -> None: ...

    async def on_event_hook_teardown(self) -> None: ...

    def to_json(self) -> dict[str, Any]:
        return {
            "event_hook_id": str(self.event_hook_id),
            "label": self.label,
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "version": str(self.version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "component_dependencies": list(map(str, self.component_dependencies)),
            "event_types": list(map(str, self.event_types)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
        }
