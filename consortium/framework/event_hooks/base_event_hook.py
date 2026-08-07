import pathlib
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
from consortium.framework._core.event_logging.event_log import EventLog
from consortium.framework._core.event_logging.event_logger import EventLogger
from consortium.framework._core.framework_exceptions.event_hooks_framework_exceptions import (
    EmptyEventHookLabelError,
    InvalidEventHookConfigurationParameterTypeError,
    InvalidEventHookDependencyVersionSpecifierError,
    InvalidEventHookVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingEventHookConfigurationParameterError,
)
from consortium.framework._core.utils import resolve_component_filepath
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.utils import construct_services_dataclass


class _EventHookMetadataModel(ComponentMetadataModel):
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
        event_types: Set of event types declared in the hook's class body, subscribed
            to when the hook is loaded. This is the declaration only: read
            `subscribed_event_types` for what the hook currently handles.
        subscribed_event_types: Read-only view of the event types the hook is
            subscribed to right now, including any changes made at runtime through
            `subscribe_to_event_type` and `unsubscribe_from_event_type`.
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
        event_logger: Event-hook-specific event logger used to record structured,
            client-facing events (successes, failures, informational messages).
            Entries are optionally mirrored to the hook's system logger.
    """

    _component_metadata_model = _EventHookMetadataModel
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

    # The class body declaration and only that: metadata validation reads it off the
    # class before any instance exists. It is never the runtime truth, since a hook can
    # change its subscriptions once it is running. What the hook actually handles lives
    # on the instance, behind `subscribed_event_types`.
    event_types: set[EventType] | None = None

    def __init__(self):
        self.event_hook_id: uuid.UUID = uuid.uuid4()
        self.logger = logger.bind(
            logger_name=f"Event Hook - {self}",
        )
        self.event_logger: EventLogger = EventLogger(
            event_log=EventLog(subject_id=self.event_hook_id),
            system_logger=self.logger,
        )
        self.environment: types.SimpleNamespace = types.SimpleNamespace()
        # Per-instance copy of the declaration, backing `subscribed_event_types`.
        # Without this, two instances of the same hook class would share (and mutate)
        # one set. Declarations are written as plain strings, so they are coerced here
        # to keep the view homogeneous with what `subscribe_to_event_type` adds.
        # Metadata validation has already rejected anything that is not a valid
        # `EventType`.
        self._event_types: set[EventType] = {
            EventType(event_type) for event_type in (type(self).event_types or set())
        }
        # Whether the events service currently holds registrations for this hook. Only
        # true between the registry finishing the load and starting the unload, which is
        # the window in which subscription changes have to be mirrored into the service
        # to take effect. Outside it, updating `_event_types` is enough because the
        # registry registers from the view once the load completes.
        self._is_dispatch_registered: bool = False

        super().__init__()

    def __init_subclass__(cls, **kwargs):
        # Frozen so that `self.event_types.add(...)` raises instead of quietly mutating
        # the declaration shared by every instance of the class while leaving the hook's
        # own subscriptions untouched. Metadata validation coerces it back to a set.
        cls.event_types = frozenset(cls.event_types or set())
        cls.root_directory = pathlib.Path(
            resolve_component_filepath(cls),
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
            f"subscribed_event_types={self.subscribed_event_types!r}"
            f")"
        )

    # Returns a frozenset rather than `_event_types` itself so that a caller mutating
    # what it gets back cannot silently disagree with dispatch: the events service holds
    # its own registrations, and a change made here would never reach them. Being a
    # setter-less property, the name cannot be rebound on an instance either.
    @property
    def subscribed_event_types(self) -> frozenset[EventType]:
        """The event types this hook is currently subscribed to.

        Starts out as the set declared in the hook's class body and reflects every
        subsequent `subscribe_to_event_type` and `unsubscribe_from_event_type` call.

        Returns:
            A read-only view of the currently subscribed event types.
        """
        return frozenset(self._event_types)

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

    def subscribe_to_event_type(self, event_type: EventType) -> None:
        """Subscribes the hook to an additional event type.

        The event type appears in `subscribed_event_types` immediately and the hook
        starts receiving it as soon as it is running. Safe to call at any point in the
        hook's lifecycle, including from `on_setup` and from `on_triggered`. Subscribing
        to an event type the hook already handles is a no-op.

        This is the only supported way to change subscriptions.
        `subscribed_event_types` is read-only, since a set that dispatch does not read
        back would silently disagree with what the hook actually receives.

        Args:
            event_type: The event type to start receiving.

        Raises:
            InvalidEventTypeError: If the provided event type does not correspond to a
                valid `EventType` member.
            EventHandlerAlreadyRegisteredError: If the hook is already registered for
                the event type with the events service.
        """
        # Imported here rather than at module scope: the events service exceptions
        # module imports from `consortium.framework.event_hooks`, so importing it at the
        # top would close an import cycle through this package's `__init__`.
        from consortium.server.exceptions.service_exceptions.events_service_exceptions import (
            InvalidEventTypeError,
        )

        try:
            event_type = EventType(event_type)
        except ValueError:
            raise InvalidEventTypeError(event_type) from None

        if event_type in self._event_types:
            return
        # Mirror into the events service only while it holds this hook's registrations.
        # Before the load completes the registry has not registered anything yet and
        # will read the view afterwards, so registering here too would double up.
        if self._is_dispatch_registered:
            self.services.events_service.register_event_handler_to_event_type(
                event_type=event_type,
                event_handler=self.on_triggered,
            )
        self._event_types.add(event_type)

    def unsubscribe_from_event_type(self, event_type: EventType) -> None:
        """Unsubscribes the hook from an event type.

        The event type is removed from `subscribed_event_types` and the hook stops
        receiving it immediately. Safe to call at any point in the hook's lifecycle.
        Unsubscribing from an event type the hook does not handle is a no-op.

        Args:
            event_type: The event type to stop receiving.

        Raises:
            EventHandlerNotRegisteredError: If the hook is running but the events
                service holds no registration for the event type.
        """
        if event_type not in self._event_types:
            return
        if self._is_dispatch_registered:
            self.services.events_service.deregister_event_handler_from_event_type(
                event_type=event_type,
                event_handler=self.on_triggered,
            )
        self._event_types.discard(EventType(event_type))

    def to_json(
        self, limit: int = 10, offset: int | None = None
    ) -> dict[str, JsonValue]:
        """Serialize the event hook's metadata to a JSON-compatible dictionary.

        Args:
            limit: Maximum number of event log entries to include.
            offset: Sequence offset to start the event log window from. If None, the
                tail (most recent entries up to limit) is returned.

        Returns:
            A dictionary containing the event hook ID, label, name, description,
            authors, version, framework compatibility, component dependencies,
            subscribed event types, third-party dependencies, and event log.
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
            "event_types": list(map(str, self.subscribed_event_types)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
            "event_log": self.event_logger.to_json(limit=limit, offset=offset),
        }

    def to_json_reference(self) -> dict[str, JsonValue]:
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
