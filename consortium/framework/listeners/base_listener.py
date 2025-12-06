# import json
import sys
import traceback
import uuid

# from abc import ABC, abstractmethod
from datetime import datetime
from types import SimpleNamespace
from typing import Any, get_type_hints

from loguru import logger
from pydantic import BaseModel, JsonValue, ValidationError

from consortium.framework._components import (
    ComponentLifeCycle,
    ComponentLifeCycleFatalContext,
)
from consortium.framework.exceptions.listeners_framework_exceptions import (  # ListenerStartError,; ListenerStopError,
    ListenerRuntimeError,
)
from consortium.framework.listeners._agents_manager import AgentsManager

# from consortium.framework.listeners._listener_status import (
#     ListenerState,
#     ListenerStatus,
# )
# from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.server.exceptions.framework_exceptions.components_framework_exceptions import (
    ComponentAlreadyStartedError,
    ComponentNotRunningError,
    ComponentStartError,
    ComponentStopError,
)
from consortium.server.exceptions.framework_exceptions.listeners_framework_exceptions import (  # ListenerRuntimeError as ListenerRuntimeFrameworkError,
    InvalidListenerConfigurationParameterTypeError,
    ListenerAlreadyStartedError,
    ListenerCreationParameterTypeError,
    ListenerNotRunningError,
    ListenerStartError as ListenerStartFrameworkError,
    ListenerStopError as ListenerStopFrameworkError,
    MissingListenerConfigurationParameterError,
)
from consortium.server.server_logging import LoggerType

# import pathlib


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
        status (ListenerStatus): Current listener state and any error information if
            the listener has encountered issues.
        datetime_created (datetime): Timestamp for when a particular listener instance
            was created.
        environment (SimpleNamespace): Namespace for storing listener-specific variables
            that can be shared between user-defined methods without naming conflicts.
        agents_manager (AgentsManager): Internal manager for handling connected agents'
            lifecycles and operations.
        logger (loguru.Logger): Listener-specific logger instance, automatically tagged
            with the listener's name and ID for easy identification in logs.
        creating_listener_template (BaseListenerTemplate | None): Reference to the
            listener template that created this instance. Set automatically during
            creation through a template.
    """

    # listener_type: BaseListenerType = None

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

        try:
            _BaseListenerParametersModel(
                name=name,
                description=description,
                endpoint=endpoint,
                parameters=parameters,
            )
        except ValidationError as exc:
            for err in exc.errors():
                raise ListenerCreationParameterTypeError(
                    listener_str=sys.modules[self.__module__].__file__,
                    parameter_name=".".join(str(loc) for loc in err["loc"]),
                    parameter_type=get_type_hints(_BaseListenerParametersModel)[
                        err["loc"]
                    ],
                ) from None

        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.parameters = parameters

        self.datetime_created = datetime.now()
        self.listener_id = uuid.uuid4()
        self.environment = SimpleNamespace()
        self.agents_manager = AgentsManager()
        self.logger = logger.bind(
            logger_name=f"Listener - {self}",
            logger_type=LoggerType.LISTENER_LOGGER,
        )

        super().__init__()

    def __str__(self) -> str:
        return f"{self.name} ({self.listener_id})"

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

    async def on_errored(self, runtime_error: ListenerRuntimeError) -> None:
        self.logger.error(runtime_error)

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
        self.logger.opt(ansi=True).error(
            "<bold><red>Fatal error occurred within plugin while it was {}:</></>\n{}",
            ctx_to_str_map[fatal_context],
            traceback.format_exc(),
        )

    async def start(self) -> None:
        try:
            await super().start()
        except ComponentAlreadyStartedError:
            raise ListenerAlreadyStartedError(
                listener_str=str(self),
            )
        except ComponentStartError as exc:
            raise ListenerStartFrameworkError(
                listener_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            )

    async def stop(self) -> None:
        try:
            await super().stop()
        except ComponentNotRunningError:
            raise ListenerNotRunningError(
                listener_str=str(self),
            )
        except ComponentStopError as exc:
            raise ListenerStopFrameworkError(
                listener_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            )

    async def cancel(self) -> None:
        try:
            await super().cancel()
        except ComponentNotRunningError:
            raise ListenerNotRunningError(
                listener_str=str(self),
            )

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
                for agent in self.agents_manager.get_all_connected_agents()
            ],
            # The `creating_listener_template` class attribute is assigned to the
            # listener class at runtime by its associated listener template when it is
            # subclassed from the base listener template class. See
            # `consortium/framework/base_listener_template.py`.
            "creating_listener_template": {
                "listener_template_id": str(
                    self.creating_listener_template.listener_template_id,
                ),
                "name": self.creating_listener_template.name,
            },
        }

        # if not isinstance("name", str):
        #     # The listener is identified by its name, but at this point we are still
        #     # validating the name parameter, so we refer to it by its filepath for now.
        #     raise ListenerCreationParameterTypeError(
        #         listener_str=sys.modules[self.__module__].__file__,
        #         parameter_name="name",
        #         parameter_type="str",
        #     )
        # if not isinstance("description", str):
        #     raise ListenerCreationParameterTypeError(
        #         listener_str=name,
        #         parameter_name="description",
        #         parameter_type="str",
        #     )
        # if not isinstance("endpoint", str):
        #     raise ListenerCreationParameterTypeError(
        #         listener_str=name,
        #         parameter_name="endpoint",
        #         parameter_type="str",
        #     )
        # try:
        #     json.dumps(parameters)
        # except json.JSONDecodeError:
        #     raise ListenerCreationParameterTypeError(
        #         listener_str=name,
        #         error_message=(
        #             "The parameter 'parameters' must be a dictionary with string keys "
        #             "and values that are either: str, int, float, bool, None, lists of "
        #             "these types, or nested dictionaries of the same structure to "
        #             "ensure JSON serializability."
        #         ),
        #     )
        # self.status = ListenerStatus()
        # self.stop_listener_event = asyncio.Event()
        # # Asyncio type tasks are held by a weak reference by default, so they can be
        # # garbage collected at any time mid-execution, to prevent this we have to store
        # # a reference of the task in a variable. We declare the variable here and assign
        # # it in start_listener() later on.
        # self._listener_task = None

    # async def start(self) -> None:
    #     if self.status.state in (ListenerState.STARTED or ListenerState.RUNNING):
    #         raise ListenerAlreadyStartedError(
    #             listener_str=str(self),
    #             error_message=(
    #                 "The listener cannot be started because it is already started or "
    #                 "running."
    #             ),
    #         )
    #
    #     # Clear the signal to the listener to stop running if it is set, so it won't
    #     # instantly stop.
    #     self.stop_listener_event.clear()
    #
    #     # The listener is now started.
    #     self.status._transition_to_started()
    #     try:
    #         await self.on_started()
    #     # ListenerStartError is raised within on_listener_started() to abort the
    #     # listener start process if preconditions are not met.
    #     except ListenerStartError as exc:
    #         # The listener is now initialized.
    #         self.status._transition_to_initialized()
    #         raise ListenerStartFrameworkError(
    #             listener_str=str(self),
    #             error_message=exc.message,
    #             detail=exc.detail,
    #         ) from None
    #     except Exception as exc:
    #         self.logger.opt(ansi=True).error(
    #             "<bold><red>{}</></>",
    #             traceback.format_exc(),
    #         )
    #         # The listener is now fatally errored.
    #         self.status._transition_to_fatal(listener=str(self), exception=exc)
    #         raise exc
    #
    #     self._listener_task = asyncio.create_task(self._run_listener())
    #
    # async def stop(self) -> None:
    #     if self.status.state != ListenerState.RUNNING:
    #         raise ListenerNotRunningError(
    #             listener_str=str(self),
    #             error_message=(
    #                 "The listener cannot be stopped because it is not running."
    #             ),
    #         )
    #
    #     try:
    #         await self.on_stopped()
    #     # ListenerStopError is raised within on_listener_stopped() to abort the
    #     # listener stop process if preconditions are not met.
    #     except ListenerStopError as exc:
    #         # The listener has not changed from its running state.
    #         self.status._transition_to_running()
    #         raise ListenerStopFrameworkError(
    #             listener_str=str(self),
    #             error_message=exc.message,
    #             detail=exc.detail,
    #         )
    #     except Exception as exc:
    #         self.logger.opt(ansi=True).error(
    #             "<bold><red>{}</></>",
    #             traceback.format_exc(),
    #         )
    #         # The listener is now fatally errored.
    #         self.status._transition_to_fatal(listener=str(self), exception=exc)
    #         raise exc
    #
    #     # Signal to the listener to stop running.
    #     self.stop_listener_event.set()
    #
    # async def cancel(self) -> None:
    #     if self.status.state != ListenerState.RUNNING:
    #         raise ListenerNotRunningError(
    #             listener_str=str(self),
    #             error_message=(
    #                 "The listener cannot be cancelled because it is not running."
    #             ),
    #         )
    #
    #     # Cancel the listener.
    #     self._listener_task.cancel()
    #
    #     # Wait for the task to finish. Then remove the task reference.
    #     while not self._listener_task.done():
    #         await asyncio.sleep(0.1)
    #     self._listener_task = None
    #
    #     try:
    #         await self.on_cancelled()
    #     except Exception as exc:
    #         self.logger.opt(ansi=True).error(
    #             "<bold><red>{}</></>",
    #             traceback.format_exc(),
    #         )
    #         # The listener is now fatally errored.
    #         self.status._transition_to_fatal(listener=str(self), exception=exc)
    #         raise exc
    #
    # async def _run_listener(self):
    #     try:
    #         try:
    #             # The listener is now running.
    #             self.status._transition_to_running()
    #
    #             await self.on_running()
    #
    #             # The listener is now stopped.
    #             self.status._transition_to_stopped()
    #             self._listener_task = None
    #         except asyncio.CancelledError:
    #             # The listener is now cancelled
    #             self.status._transition_to_cancelled()
    #         except ListenerRuntimeError as exc:
    #             framework_exc = ListenerRuntimeFrameworkError(
    #                 listener_str=str(self),
    #                 error_message=exc.message,
    #                 detail=exc.detail,
    #             )
    #             # The listener is now errored.
    #             self.status._transition_to_errored(exception=framework_exc)
    #             try:
    #                 # `on_listener_errored()` should receive the unwrapped 'raw'
    #                 # exception.
    #                 await self.on_errored(exception=exc)
    #             except Exception as exc:
    #                 self.logger.opt(ansi=True).error(
    #                     "<bold><red>{}</></>",
    #                     traceback.format_exc(),
    #                 )
    #                 # The listener is now fatally errored.
    #                 self.status._transition_to_fatal(
    #                     listener=str(self),
    #                     exception=exc,
    #                 )
    #     except Exception as exc:
    #         self.logger.opt(ansi=True).error(
    #             "<bold><red>{}</></>",
    #             traceback.format_exc(),
    #         )
    #         self.status._transition_to_fatal(listener=str(self), exception=exc)
    #         # The listener is now fatally errored.
    #         try:
    #             await self.on_errored(exc)
    #         except Exception as exc:
    #             self.logger.opt(ansi=True).error(
    #                 "<bold><red>{}</></>",
    #                 traceback.format_exc(),
    #             )
    #             self.status._transition_to_fatal(listener=str(self), exception=exc)
