import pathlib
import sys
import types
import uuid

from loguru import logger
from pydantic import JsonValue

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.components import (
    ComponentMetadata,
    ComponentMetadataExceptions,
    ComponentMetadataModel,
)
from consortium.framework._core.framework_exceptions.event_hooks_framework_exceptions import (
    EmptyEventHookLabelError,
    InvalidEventHookConfigurationParameterTypeError,
    InvalidEventHookDependencyVersionSpecifierError,
    InvalidEventHookVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingEventHookConfigurationParameterError,
)
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.utils import construct_services_dataclass


class _EventHookModel(ComponentMetadataModel):
    event_types: set[EventType] | None = None


class BaseEventHook(ComponentMetadata):
    """Base class for implementing custom event hooks in the Consortium framework.

    Event hooks allow components to react to specific framework events by executing
    user-defined logic. All custom event hooks must inherit from this class and
    implement the required event hook methods.

    Attributes:
        event_hook_id: Unique framework-wide identifier for this event hook instance,
            generated as a UUID4.
        name: Human-readable name for identifying this event hook.
        description: Brief description of the event hook's purpose and functionality.
        authors: Set of authors associated with this event hook.
        version: Version of the event hook, specified using a valid PEP 440 version
            string.
        compatible_framework_version: Framework version specifier defining which
            versions of Consortium this event hook is compatible with.
        event_types: Set of event types that this hook subscribes to and will be
            triggered by.
        component_dependencies: Version-pinned dependencies on other framework
            components, defined using PEP 440 specifiers.
        third_party_dependencies: Third-party library dependencies required for this
            event hook to function.
        root_directory: Filesystem path to the project directory containing
            this event hook's source code.
        environment: Namespace for storing hook-specific state shared across event
            invocations without naming conflicts.
        services: Namespace providing programmatic access to server-level framework
            services.
        logger: Event-hook-specific logger instance, automatically tagged with the
            hook's name and ID for traceability in logs.
    """

    _METADATA_MODEL = _EventHookModel

    # Raise event hook framework exceptions directly from the shared metadata validation
    # instead of raising generic component exceptions and remapping them in __init_subclass__.
    _component_metadata_exceptions = ComponentMetadataExceptions(
        missing_configuration_parameter=MissingEventHookConfigurationParameterError,
        invalid_configuration_parameter_type=InvalidEventHookConfigurationParameterTypeError,
        empty_label=EmptyEventHookLabelError,
        invalid_version=InvalidEventHookVersionError,
        invalid_framework_version_specifier=InvalidFrameworkVersionSpecifierError,
        invalid_dependency_version_specifier=InvalidEventHookDependencyVersionSpecifierError,
    )

    event_types: set[EventType] | None = None

    def __init__(self):
        self.event_hook_id: uuid.UUID = uuid.uuid4()
        self.logger = logger.bind(
            logger_name=f"Event Hook - {self}",
        )
        self.environment: types.SimpleNamespace = types.SimpleNamespace()

        super().__init__()

    def __init_subclass__(cls, **kwargs):
        cls.event_types = cls.event_types or set()
        cls.root_directory = pathlib.Path(
            sys.modules[cls.__module__].__file__,
        ).parents[0]
        cls.services = construct_services_dataclass(server_singletons=server_singletons)

        cls._validate_metadata()

        super().__init_subclass__(**kwargs)

    def __str__(self):
        return f"'{self.name}' ({self.event_hook_id})"

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

    async def on_setup(self) -> None:
        """Called once when the event hook is initialized.

        Override to perform any setup or resource allocation required before
        the hook begins handling events.
        """

    async def on_triggered(self, event: Event) -> None:
        """Called whenever one of the subscribed event types fires.

        Override to implement custom logic for processing the event and performing
        any related actions.

        Args:
            event: The event object carrying details about what occurred, including
                the event type and any associated payload data.
        """

    async def on_teardown(self) -> None:
        """Called when the event hook is being shut down.

        Override to release resources or perform cleanup operations before the
        hook stops receiving events.
        """

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the event hook's metadata to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the event hook ID, label, name, description,
            authors, version, framework compatibility, component dependencies,
            subscribed event types, and third-party dependencies.
        """
        return {
            "event_hook_id": str(self.event_hook_id),
            "label": self.label,
            "name": self.name,
            "description": self.description,
            "authors": list(self.authors),
            "version": str(self.version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "component_dependencies": list(map(str, self.component_dependencies)),
            "event_types": list(map(str, self.event_types)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
        }

    def to_json_reference(self) -> dict[str, str]:
        """Serialize a compact reference to this event hook.

        Returns:
            A dictionary containing only the event hook ID, label, and name, suitable
            for embedding as a lightweight foreign key reference in other JSON objects.
        """
        return {
            "event_hook_id": str(self.event_hook_id),
            "label": self.label,
            "name": self.name,
        }
