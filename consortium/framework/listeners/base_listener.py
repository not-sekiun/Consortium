import uuid
from datetime import datetime
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, get_type_hints

from loguru import logger
from pydantic import BaseModel, JsonValue, ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.components import (
    ComponentLifeCycle,
    ComponentLifeCycleExceptions,
    ComponentLifeCyclePhase,
)
from consortium.framework._core.event_logging.event_log import EventLog
from consortium.framework._core.event_logging.event_logger import EventLogger
from consortium.framework._core.framework_exceptions.listeners_framework_exceptions import (
    ListenerAlreadyRunningError,
    ListenerCreationParameterTypeError,
    ListenerFatalError,
    ListenerNotRunningError,
    ListenerRuntimeError,
    ListenerStartError,
    ListenerStopError,
)
from consortium.framework._core.utils import resolve_validation_error_parameter
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.connected_agents_service import ConnectedAgentsService
from consortium.server.utils import (
    construct_services_dataclass,
    generate_random_human_readable_name,
    utc_now,
)

if TYPE_CHECKING:
    from consortium.framework.listeners.base_listener_template import (
        BaseListenerTemplate,
    )
    from consortium.framework.listeners.base_listener_type import BaseListenerType
    from consortium.server.objects.agent_objects import Agent


class _BaseListenerParametersModel(BaseModel):
    name: str
    description: str
    endpoint: str
    parameters: dict[str, JsonValue]


class BaseListener(ComponentLifeCycle):
    """Base class for implementing custom listeners in the Consortium framework.

    Listeners manage the complete lifecycle of connected agents, including registration,
    check-ins, task distribution, and result collection. All custom listeners must
    inherit from this class and implement the required base listener hook methods.

    Attributes:
        listener_id: Unique framework-wide identifier for this listener instance,
            generated as a UUID4.
        name: Human-readable name for identifying this listener instance. Either
            supplied explicitly at creation time or randomly generated. It is display
            metadata only and is never derived from, or kept in sync with, the
            listener's parameters.
        description: Brief description of the listener's purpose and functionality.
        endpoint: Network endpoint identifier, typically a socket address, that
            uniquely identifies where this listener can be reached.
        listener_type: Type descriptor that defines which agent types are compatible
            with this listener.
        parameters: Configuration parameters used to customize the listener's behavior.
            Available parameters are defined in the associated listener template.
        datetime_created: Timestamp recording when this listener instance was created.
        environment: Namespace for storing listener-specific state shared between
            user-defined methods without naming conflicts.
        connected_agents_service: Internal manager for handling the lifecycles and
            operations of agents connected to this listener.
        logger: Listener-specific system logger instance, automatically tagged with the
            listener's name and ID for easy identification in logs.
        event_logger: Listener-specific event logger used to record structured,
            client-facing lifecycle events (successes, failures, informational
            messages, progress updates). Entries are optionally mirrored to the
            listener's system logger.
        creating_listener_template: Reference to the listener template that created
            this instance. Set automatically during creation.
    """

    creating_listener_template: BaseListenerTemplate
    listener_type: BaseListenerType

    # Raise listener errors directly from the shared lifecycle instead of raising generic
    # component errors and remapping them here, which would format the message twice.
    _component_life_cycle_exceptions = ComponentLifeCycleExceptions(
        start=ListenerStartError,
        stop=ListenerStopError,
        runtime=ListenerRuntimeError,
        fatal=ListenerFatalError,
        not_running=ListenerNotRunningError,
        already_running=ListenerAlreadyRunningError,
    )

    def __init__(
        self,
        name: str | None = None,
        description: str = "",
        endpoint: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a listener instance with the specified configuration.

        While this constructor can be called directly, it is strongly recommended to
        create listeners through their associated listener templates. Templates ensure
        proper validation of parameters and configuration before instantiation.

        Args:
            name: Human-readable name for identifying this listener. When `None` a
                random human-readable name is generated. The name is display metadata
                that is independent of `parameters`; it is never derived from them.
            description: Brief description of the listener's purpose.
            endpoint: Network endpoint identifier where the listener will be accessible,
                typically a socket address like "http://0.0.0.0:8080".
            parameters: Dictionary of configuration parameters that customize the
                listener's behavior. Available parameters are defined by the listener
                template.

        Raises:
            ListenerCreationParameterTypeError: If any parameter has an invalid type
                according to the expected schema.
        """
        if parameters is None:
            parameters = {}
        # A listener that was not given an explicit name gets a generated one. Names are
        # never resolved from `parameters`, so an unnamed listener has nothing else to
        # fall back on.
        if name is None:
            name = generate_random_human_readable_name()
        # Manually validate name first so we can reference the name in subsequent
        # validation errors
        if not isinstance(name, str):
            raise ListenerCreationParameterTypeError(
                listener_str=self.__class__.__name__,
                parameter_name="name",
                parameter_type=str(str),
            ) from None

        try:
            _BaseListenerParametersModel(
                name=name,
                description=description,
                endpoint=endpoint,
                parameters=parameters,
            )
        except ValidationError as exc:
            parameter_name, parameter_type = resolve_validation_error_parameter(
                exc=exc,
                parameter_types=get_type_hints(_BaseListenerParametersModel),
            )
            raise ListenerCreationParameterTypeError(
                listener_str=name,
                parameter_name=parameter_name,
                parameter_type=parameter_type,
            ) from None

        self.name: str = name
        self.description: str = description
        self.endpoint: str = endpoint
        self.parameters: dict[str, Any] = parameters

        self.datetime_created: datetime = utc_now()
        self.listener_id: uuid.UUID = uuid.uuid4()
        self.environment: SimpleNamespace = SimpleNamespace()
        self.connected_agents_service: ConnectedAgentsService = ConnectedAgentsService(
            listener_id=self.listener_id,
        )
        self.logger = logger.bind(
            logger_name=f"Listener - {self}",
            logger_type=LoggerType.LISTENER_LOGGER,
        )
        self.event_logger = EventLogger(
            event_log=EventLog(subject_id=self.listener_id),
            system_logger=self.logger,
        )

        super().__init__()

    def __init_subclass__(cls, **kwargs):
        cls.services = construct_services_dataclass(server_singletons=server_singletons)
        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({self.listener_id})"

    def __repr__(self) -> str:
        return (
            f"Listener("
            f"name={self.name!r}, "
            f"description={self.description!r}"
            f"endpoint={self.endpoint!r}, "
            f"parameters={self.parameters!r}"
            f")"
        )

    @property
    def connected_agents(self) -> list[Agent]:
        """All agents currently connected to this listener.

        Returns:
            A list of Agent instances that have registered with and are actively
            managed by this listener.
        """
        return self.connected_agents_service.get_all_agents()

    async def on_started(self) -> None:
        """Called once immediately after the listener enters the running state."""
        ...

    async def on_running(self) -> None:
        """Called on each iteration of the listener's main loop while running."""
        ...

    async def on_completed(self) -> None:
        """Called when the listener's main loop exits normally without being stopped."""
        ...

    async def on_stopped(self) -> None:
        """Called once after the listener has been successfully stopped."""
        ...

    async def on_cancelled(self) -> None:
        """Called once after the listener run has been cancelled."""
        ...

    async def on_errored(self, error: ListenerRuntimeError) -> None:
        """Called when a runtime error occurs during the listener's execution.

        Override to add custom error handling or alerting logic in addition to or
        instead of the default behaviour of recording the error as a failure event.

        Args:
            error: The runtime error describing what went wrong during listener
                execution, including the error message and any diagnostic detail.
        """
        # Recording through the event logger both surfaces the failure in the
        # client-facing event log and mirrors it to the listener's system logger.
        self.event_logger.failure(str(error))

    async def on_fatal(
        self,
        exc: Exception,
        phase: ComponentLifeCyclePhase,
    ) -> None:
        """Called when an unhandled exception causes the listener to terminate fatally.

        Override to add custom alerting or cleanup logic when a fatal failure occurs.
        The default implementation logs the full traceback at error level.

        Args:
            exc: The unhandled exception that triggered the fatal shutdown.
            phase: The lifecycle phase during which the fatal exception
                occurred (starting, running, stopping, cancelling, or error handling).
        """
        phase_to_str_map = {
            ComponentLifeCyclePhase.START: "starting",
            ComponentLifeCyclePhase.RUNNING: "running",
            ComponentLifeCyclePhase.STOP: "stopping",
            ComponentLifeCyclePhase.CANCEL: "being cancelled",
            ComponentLifeCyclePhase.ERROR: "handling a runtime error",
        }
        # Pass the exception object rather than a pre-rendered traceback string: it
        # reaches sinks as `record["exception"]`, so a registered sink can walk the
        # exception and its `__cause__` chain instead of parsing text out of the message.
        self.logger.opt(colors=True, exception=exc).error(
            "<bold><red>Fatal error occurred within listener {} while it was {}:</></>",
            str(self),
            phase_to_str_map[phase],
        )

    # start(), stop() and cancel() below add no behaviour and exist purely to carry their
    # documentation. The documentation generator infers docstrings statically and does not
    # follow the MRO, so the listener specific `Raises:` entries have to be physically
    # present on this class to be published.
    #
    # Do NOT reintroduce a try/except here to convert component errors into listener
    # errors. The lifecycle already raises the listener errors directly via
    # `_component_life_cycle_exceptions`; catching and re-raising would pass an already
    # formatted message back through a second template and nest the prefix.

    async def start(self) -> None:
        """Start the listener and begin accepting agent connections.

        Raises:
            ListenerAlreadyRunningError: If the listener is already in a running state.
            ListenerStartError: If the listener fails to start due to a lifecycle error.
            ListenerFatalError: If an unhandled exception escapes `on_started`, leaving
                the listener in a fatal state. The original exception is chained onto it
                as `__cause__`.
        """
        await super().start()

    async def stop(self) -> None:
        """Stop the listener and cease accepting new agent connections.

        Raises:
            ListenerNotRunningError: If the listener is not currently running.
            ListenerStopError: If the listener fails to stop cleanly.
            ListenerFatalError: If an unhandled exception escapes `on_stopped`, leaving
                the listener in a fatal state. The original exception is chained onto it
                as `__cause__`.
        """
        await super().stop()

    async def cancel(self) -> None:
        """Cancel the listener run immediately.

        Raises:
            ListenerNotRunningError: If the listener is not currently running.
            ListenerFatalError: If an unhandled exception escapes `on_cancelled`, leaving
                the listener in a fatal state. The original exception is chained onto it
                as `__cause__`.
        """
        await super().cancel()

    def to_json(
        self,
        limit: int = 10,
        offset: int | None = None,
        include_event_log_entries: bool = True,
    ) -> dict[str, JsonValue]:
        """Serialize the listener's current state to a JSON-compatible dictionary.

        Args:
            limit: Maximum number of event log entries to include.
            offset: Sequence offset to start the event log window from. If None, the
                tail (most recent entries up to limit) is returned.
            include_event_log_entries: When False, the event log's entries list is
                omitted (its total count and current progress are still included). Used
                by collection endpoints to keep list responses bounded.

        Returns:
            A dictionary containing the listener ID, name, description, endpoint,
            listener type, parameters, status, creation timestamp, event log,
            connected agents as references, and the creating listener template as a
            reference.
        """
        return {
            "listener_id": str(self.listener_id),
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "listener_type": self.listener_type.to_json(),
            "parameters": self.parameters,
            "status": self.status.to_json(),
            "event_log": self.event_logger.to_json(
                limit=limit, offset=offset, include_entries=include_event_log_entries
            ),
            "datetime_created": self.datetime_created.isoformat(),
            "connected_agents": [
                agent.to_json_reference() for agent in self.connected_agents
            ],
            # `creating_listener_template` is assigned to the listener class by the
            # listener profile loader at load time.
            "creating_listener_template": self.creating_listener_template.to_json_reference(),
        }

    def to_json_reference(self) -> dict[str, JsonValue]:
        """Serialize a compact reference to this listener.

        Returns:
            A dictionary containing only the listener ID, name, and listener type,
            suitable for embedding as a lightweight foreign key reference in other
            JSON objects.
        """
        # A live reference: the listener is in memory here, so the full listener type
        # descriptor is embedded, mirroring `Agent.to_json_reference`.
        return {
            "listener_id": str(self.listener_id),
            "name": self.name,
            "listener_type": self.listener_type.to_json(),
        }
