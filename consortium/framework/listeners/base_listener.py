import traceback
import uuid
from datetime import datetime
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, get_type_hints

from loguru import logger
from pydantic import BaseModel, JsonValue, ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.components import (
    ComponentLifeCycle,
    ComponentLifeCycleFatalContext,
)
from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    ComponentAlreadyRunningError,
    ComponentNotRunningError,
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)
from consortium.framework._core.framework_exceptions.listeners_framework_exceptions import (
    ListenerAlreadyRunningError,
    ListenerCreationParameterTypeError,
    ListenerNotRunningError,
    ListenerRuntimeError,
    ListenerStartError,
    ListenerStopError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.connected_agents_service import ConnectedAgentsService
from consortium.server.utils import construct_services_dataclass

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
        listener_id (uuid.UUID): Unique framework-wide identifier for this listener
            instance, generated as a UUID4.
        name (str): Human-readable name for identifying this listener instance.
        description (str): Brief description of the listener's purpose and functionality.
        endpoint (str): Network endpoint identifier, typically a socket address, that
            uniquely identifies where this listener can be reached.
        listener_type (BaseListenerType): Type descriptor that defines which agent types
            are compatible with this listener.
        parameters (dict[str, Any]): Configuration parameters used to customize the
            listener's behavior. Available parameters are defined in the associated
            listener template.
        datetime_created (datetime): Timestamp recording when this listener instance
            was created.
        environment (SimpleNamespace): Namespace for storing listener-specific state
            shared between user-defined methods without naming conflicts.
        connected_agents_service (ConnectedAgentsService): Internal manager for handling
            the lifecycles and operations of agents connected to this listener.
        logger (loguru.Logger): Listener-specific logger instance, automatically tagged
            with the listener's name and ID for easy identification in logs.
        creating_listener_template (BaseListenerTemplate): Reference to the listener
            template that created this instance. Set automatically during creation.
    """

    creating_listener_template: BaseListenerTemplate
    listener_type: BaseListenerType

    def __init__(
        self,
        name: str = "",
        description: str = "",
        endpoint: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a listener instance with the specified configuration.

        While this constructor can be called directly, it is strongly recommended to
        create listeners through their associated listener templates. Templates ensure
        proper validation of parameters and configuration before instantiation.

        Args:
            name: Human-readable name for identifying this listener.
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
            raise ListenerCreationParameterTypeError(
                listener_str=name,
                parameter_name=str(exc.errors()[0]["loc"][0]),
                parameter_type=str(
                    get_type_hints(_BaseListenerParametersModel)[
                        exc.errors()[0]["loc"][0]
                    ]
                ),
            ) from None

        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.parameters = parameters

        self.datetime_created = datetime.now()
        self.listener_id = uuid.uuid4()
        self.environment = SimpleNamespace()
        self.connected_agents_service = ConnectedAgentsService(
            listener_id=self.listener_id,
        )
        self.logger = logger.bind(
            logger_name=f"Listener - {self}",
            logger_type=LoggerType.LISTENER_LOGGER,
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
        instead of the default error logging.

        Args:
            error: The runtime error describing what went wrong during listener
                execution, including the error message and any diagnostic detail.
        """
        self.logger.error(error)

    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
        """Called when an unhandled exception causes the listener to terminate fatally.

        Override to add custom alerting or cleanup logic when a fatal failure occurs.
        The default implementation logs the full traceback at error level.

        Args:
            exc: The unhandled exception that triggered the fatal shutdown.
            fatal_context: The lifecycle phase during which the fatal exception
                occurred (starting, running, stopping, cancelling, or error handling).
        """
        ctx_to_str_map = {
            ComponentLifeCycleFatalContext.START: "starting",
            ComponentLifeCycleFatalContext.RUNNING: "running",
            ComponentLifeCycleFatalContext.STOP: "stopping",
            ComponentLifeCycleFatalContext.CANCEL: "being cancelled",
            ComponentLifeCycleFatalContext.ERROR: "handling a runtime error",
        }
        self.logger.opt(colors=True).error(
            "<bold><red>Fatal error occurred within listener {} while it was {}:</></>\n{}",
            str(self),
            ctx_to_str_map[fatal_context],
            traceback.format_exc(),
        )

    async def start(self) -> None:
        """Start the listener and begin accepting agent connections.

        Raises:
            ListenerAlreadyRunningError: If the listener is already in a running state.
            ListenerStartError: If the listener fails to start due to a lifecycle error.
        """
        try:
            await super().start()
        except ComponentAlreadyRunningError:
            raise ListenerAlreadyRunningError(
                listener_str=str(self),
            ) from None
        except ComponentStartError as exc:
            raise ListenerStartError(
                listener_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None

    async def stop(self) -> None:
        """Stop the listener and cease accepting new agent connections.

        Raises:
            ListenerNotRunningError: If the listener is not currently running.
            ListenerStopError: If the listener fails to stop cleanly.
        """
        try:
            await super().stop()
        except ComponentNotRunningError:
            raise ListenerNotRunningError(
                listener_str=str(self),
            ) from None
        except ComponentStopError as exc:
            raise ListenerStopError(
                listener_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None

    async def cancel(self) -> None:
        """Cancel the listener run immediately.

        Raises:
            ListenerNotRunningError: If the listener is not currently running.
        """
        try:
            await super().cancel()
        except ComponentNotRunningError:
            raise ListenerNotRunningError(
                listener_str=str(self),
            ) from None

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the listener's current state to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the listener ID, name, description, endpoint,
            listener type, parameters, status, creation timestamp, connected agents
            as references, and the creating listener template as a reference.
        """
        return {
            "listener_id": str(self.listener_id),
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "listener_type": self.listener_type.to_json(),
            "parameters": self.parameters,
            "status": self.status.to_json(),
            "datetime_created": self.datetime_created.isoformat(),
            "connected_agents": [
                agent.to_json_reference() for agent in self.connected_agents
            ],
            # `creating_listener_template` is assigned to the listener class by the
            # listener profile loader at load time.
            "creating_listener_template": self.creating_listener_template.to_json_reference(),
        }

    def to_json_reference(self) -> dict[str, str]:
        """Serialize a compact reference to this listener.

        Returns:
            A dictionary containing only the listener ID and name, suitable for
            embedding as a lightweight foreign key reference in other JSON objects.
        """
        return {
            "listener_id": str(self.listener_id),
            "name": self.name,
        }

    def _construct_component_runtime_error_from_framework_runtime_error(
        self,
        error: ComponentRuntimeError,
    ) -> ListenerRuntimeError:
        return ListenerRuntimeError(
            listener_str=str(self),
            error_message=error.message,
            detail=error.detail,
        )

    def _construct_component_runtime_error_from_unhandled_exception(
        self,
        exc: Exception,
    ) -> ListenerRuntimeError:
        return ListenerRuntimeError(
            listener_str=str(self),
            error_message=(
                f"An unhandled exception was raised while running. "
                f"{type(exc).__name__}: {exc}"
            ),
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )
