import pathlib
import sys
import types
import uuid
from typing import Any

from loguru import logger

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
import consortium.server.server_singletons as server_singletons
from consortium.framework._components import ComponentMetadata, ComponentMetadataModel
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.framework.utils.exception_utils import remap_exception
from consortium.server.exceptions.framework_exceptions.event_hooks_framework_exceptions import (
    EmptyEventHookLabelError,
    InvalidEventHookConfigurationParameterTypeError,
    InvalidEventHookDependencyVersionSpecifierError,
    InvalidEventHookVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingEventHookConfigurationParameterError,
)


class _EventHookModel(ComponentMetadataModel):
    event_types: set[EventType] | None = None


class BaseEventHook(ComponentMetadata):
    """
    Base class for implementing custom event hooks in the Consortium framework.

    Event hooks allow components to react to specific framework events by executing
    user-defined logic. All custom event hooks must inherit from this class and
    implement the required event hook methods.

    Attributes:
        event_hook_id (uuid.UUID): Unique framework-wide identifier for this event
            hook instance, generated as a UUID4.
        name (str): Human-readable name for the event hook. This is not used as a
            unique identifier within the framework.
        description (str): Brief description of the event hook's purpose and
            functionality.
        authors (set[str]): Set of authors associated with this event hook.
        version (Version): Version of the event hook, specified using a valid PEP 440
            version string.
        compatible_framework_version (SpecifierSet): Framework version specifier
            defining the versions of Consortium this event hook is compatible with.
        event_types (set[EventType]): Set of events that this hook subscribes to and
            will be triggered by.
        component_dependencies (set[str]): Version-pinned dependencies on other
            framework components, defined using PEP 440 specifiers.
        third_party_dependencies (set[str]): Third-party library dependencies required
            for this event hook to function.
        event_hook_project_folder (Path): Filesystem path to the project directory
            containing this event hook's source code.
        environment (SimpleNamespace): Namespace for storing hook-specific state shared
            across event invocations without naming conflicts.
        server_services (SimpleNamespace): Namespace providing programmatic access to
            server-level framework services.
        logger (loguru.Logger): Event-hook-specific logger instance, automatically
            tagged with the hook's name and ID for traceability in logs.
    """

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
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        cls.event_types = cls.event_types or set()
        cls.event_hook_project_folder = pathlib.Path(
            sys.modules[cls.__module__].__file__,
        ).parents[0]
        try:
            cls._validate_metadata()
        except comp_excs.ComponentsFrameworkError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.kwargs,
                exception_map=cls._EXCEPTION_MAP,
                exception_kwargs_map=cls._EXCEPTION_KWARGS_MAP,
            ) from None
        super().__init_subclass__(**kwargs)

    def __str__(self):
        return f"{self.name} ({self.event_hook_id})"

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

    async def on_event_hook_setup(self) -> None:
        """
        Executed once when the event hook is initialized. Use this method to perform
        any setup or resource allocation required before handling events.
        """

    async def on_event_hook_triggered(self, event: Event) -> None:
        """
        Executed whenever one of the subscribed events occurs. Implement custom
        logic here to process the event and perform any related actions.
        Args:
            event (Event): The event object containing details about the triggered
            event
        """

    async def on_event_hook_teardown(self) -> None:
        """
        Executed when the event hook is being shut down. Use this method to
        release resources or perform cleanup operations.
        """

    def to_json(self) -> dict[str, Any]:
        """
        Return a JSON-serializable representation of the event hook's metadata,
        """
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
