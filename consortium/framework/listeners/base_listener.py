import traceback
import uuid
from datetime import datetime
from types import SimpleNamespace
from typing import Any, get_type_hints

from loguru import logger
from pydantic import BaseModel, JsonValue, ValidationError

from consortium.framework._components import (
    ComponentLifeCycle,
    ComponentLifeCycleFatalContext,
)
from consortium.server.exceptions.consortium_exceptions.components_consortium_exceptions import (
    ComponentAlreadyRunningError,
    ComponentNotRunningError,
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)
from consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions import (
    ListenerAlreadyRunningError,
    ListenerCreationParameterTypeError,
    ListenerNotRunningError,
    ListenerRuntimeError,
    ListenerStartError,
    ListenerStopError,
)
from consortium.server.server_logging import LoggerType
from consortium.server.services.connected_agents_service import ConnectedAgentsService


class _BaseListenerParametersModel(BaseModel):
    name: str
    description: str
    endpoint: str
    # Pydantic doesn't support recursive forward reference types, so we use JsonValue
    # here.
    parameters: dict[str, JsonValue]


class BaseListener(ComponentLifeCycle):  # ABC):
    """
    Base class for implementing custom listeners in the Consortium framework.

    Listeners manage the complete lifecycle of connected agents, including registration,
    check-ins, task distribution, and result collection. All custom listeners must
    inherit from this class and implement the required base listener hook methods.

    Attributes:
        listener_id (uuid.UUID): Unique framework-wide identifier for a particular
            listener instance, generated as a UUID4.
        name (str): Human-readable name for the listener. This is not used as a unique
            identifier within the framework.
        description (str): Brief description of the listener's purpose and
            functionality.
        endpoint (str): Network endpoint identifier, typically a socket address, that
            uniquely identifies where this listener can be reached.
        listener_type (BaseListenerType): Type descriptor that defines which agent types
            are compatible with this listener.
        parameters (dict[str, Any]): Configuration parameters used to customize the
            listener's behavior. Available parameters are defined in the associated
            listener template.
        status (ListenerStatus): Current listener status and any error information if
            the listener has encountered issues.
        datetime_created (datetime): Timestamp for when a particular listener instance
            was created.
        environment (SimpleNamespace): Namespace for storing listener-specific variables
            that can be shared between user-defined methods without naming conflicts.
        connected_agents_service (ConnectedAgentsService): Internal manager for handling connected agents'
            lifecycles and operations.
        logger (loguru.Logger): Listener-specific logger instance, automatically tagged
            with the listener's name and ID for easy identification in logs.
        creating_listener_template (BaseListenerTemplate | None): Reference to the
            listener template that created this instance. Set automatically during
            creation through a template.
    """

    def __init__(
        self,
        name: str = "",
        description: str = "",
        endpoint: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize a listener instance with the specified configuration.

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
                parameter_name=exc.errors()[0]["loc"][0],
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
        self.connected_agents_service = ConnectedAgentsService()
        self.logger = logger.bind(
            logger_name=f"Listener - {self}",
            logger_type=LoggerType.LISTENER_LOGGER,
        )

        super().__init__()

    def __init_subclass__(cls, **kwargs):
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

    async def on_started(self) -> None: ...

    async def on_running(self) -> None: ...

    async def on_completed(self) -> None: ...

    async def on_stopped(self) -> None: ...

    async def on_cancelled(self) -> None: ...

    async def on_errored(self, error: ListenerRuntimeError) -> None:
        self.logger.error(error)

    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
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
        try:
            await super().cancel()
        except ComponentNotRunningError:
            raise ListenerNotRunningError(
                listener_str=str(self),
            ) from None

    def to_json(self) -> dict[str, Any]:
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
                {"agent_id": str(agent.agent_id), "name": str(agent.name)}
                for agent in self.connected_agents_service.get_all_agents()
            ],
            # `creating_listener_template` is assigned to the listener class by the
            # listener profile loader at load time.
            "creating_listener_template": {
                "listener_template_id": str(
                    self.creating_listener_template.listener_template_id,
                ),
                "label": self.creating_listener_template.label,
                "name": self.creating_listener_template.name,
            },
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
