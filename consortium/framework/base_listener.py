import asyncio
import json
import sys
import traceback
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.framework.c2_types import BaseAgentType, BaseListenerType
from consortium.framework.exceptions.listeners_framework_exceptions import (
    ListenerRuntimeError,
    ListenerSpecificAgentNotFoundError,
    ListenerStartError,
    ListenerStopError,
)
from consortium.server.exceptions.framework_exceptions.listeners_framework_exceptions import (
    EmptyListenerNameError,
    ListenerAlreadyRunningError,
    ListenerConfigurationParameterTypeError,
    ListenerCreationParameterTypeError,
    ListenerNotRunningError,
    ListenerRuntimeError as ListenerRuntimeFrameworkError,
    ListenerStartError as ListenerStartFrameworkError,
    ListenerStopError as ListenerStopFrameworkError,
    RequiredListenerConfigurationParameterNotDeclaredError,
)
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.listener_objects import ListenerState, ListenerStatus
from consortium.server.server_logging import LoggerType


class _AgentsManager:
    def __init__(self):
        self._agents_service = server_singletons.agents_service
        self._agents = {}

    async def register_new_connected_agent(
        self,
        agent_type: BaseAgentType,
        name: str = "",
        description: str = "",
        endpoint: str = "",
        is_admin: bool | None = None,
        os: str | None = None,
        version: str | None = None,
        arch: str | None = None,
        pid: int | None = None,
        locale: str | None = None,
        remote_host_address: str | None = None,
        local_host_address: str | None = None,
        agent_data: dict[str, Any] | None = None,
    ) -> Agent:
        agent = await self._agents_service.create_and_add_agent(
            agent_type=agent_type,
            name=name,
            description=description,
            endpoint=endpoint,
            is_admin=is_admin,
            os=os,
            version=version,
            arch=arch,
            pid=pid,
            locale=locale,
            remote_host_address=remote_host_address,
            local_host_address=local_host_address,
            agent_data=agent_data,
        )
        self._agents[str(agent.agent_id)] = agent
        return agent

    async def check_in_connected_agent_by_agent_id(self, agent_id: str) -> None:
        if agent_id not in self._agents:
            raise ListenerSpecificAgentNotFoundError
        await self._agents_service.check_in_agent_by_agent_id(agent_id=agent_id)

    async def deregister_connected_agent_by_agent_id(self, agent_id: str) -> None:
        if agent_id not in self._agents:
            raise ListenerSpecificAgentNotFoundError
        await self._agents_service.remove_agent_by_agent_id(agent_id=agent_id)
        self._agents.pop(str(agent_id))

    def get_all_connected_agents(self) -> list[Agent]:
        return list(self._agents.values())

    def get_connected_agent_by_agent_id(self, agent_id: str) -> Agent:
        try:
            return self._agents[agent_id]
        except KeyError:
            raise ListenerSpecificAgentNotFoundError


class BaseListener(ABC):
    listener_type: BaseListenerType

    def __init__(
        self,
        name: str = "",
        description: str = "",
        endpoint: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        if parameters is None:
            parameters = {}

        if not isinstance("name", str):
            # The listener is identified by its name, but at this point we are still
            # validating the name parameter, so we refer to it by its filepath for now.
            raise ListenerCreationParameterTypeError(
                listener_str=sys.modules[self.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not name:
            raise EmptyListenerNameError(
                listener_filepath=sys.modules[self.__module__].__file__,
            )
        # From here onwards we can refer to the listener by its assigned name.
        if not isinstance("description", str):
            raise ListenerCreationParameterTypeError(
                listener_str=name,
                parameter_name="description",
                parameter_type="str",
            )
        if not isinstance("endpoint", str):
            raise ListenerCreationParameterTypeError(
                listener_str=name,
                parameter_name="endpoint",
                parameter_type="str",
            )
        try:
            json.dumps(parameters)
        except json.JSONDecodeError:
            raise ListenerCreationParameterTypeError(
                listener_str=name,
                error_message=(
                    "The parameter 'parameters' must be a dictionary with string keys "
                    "and values that are either: str, int, float, bool, None, lists of "
                    "these types, or nested dictionaries of the same structure to "
                    "ensure JSON serializability."
                ),
            )

        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.parameters = parameters

        self.datetime_created = datetime.now()
        self.listener_id = uuid.uuid4()
        # Original status state is set to INITIALIZED.
        self.status = ListenerStatus()
        # self.environment is used to store any information that the listener may need
        # to store and share amongst its user defined methods.

        self.environment = SimpleNamespace()
        # self.stop_listener_event is used to signal to the listener runtime loop to
        # exit. The implementation of the listener runtime loop should check this event
        # periodically and exit if it is set.
        self.stop_listener_event = asyncio.Event()
        # self.agent_manager a class that allows listeners to manage the lifetime of an
        # agent from registration to checking in to deregistration, as well as to
        # manage access to agents registered locally to the specific listener.
        self.agents_manager = _AgentsManager()
        # self.listener_logger is an internal logger to use for logging within the
        # listener to standard output and log files.
        self.listener_logger = logger.bind(
            logger_name=f"Listener {self}",
            logger_type=LoggerType.LISTENER_LOGGER,
        )

        # Asyncio type tasks are held by a weak reference by default, so they can be
        # garbage collected at any time mid-execution, to prevent this we have to store
        # a reference of the task in a variable. We declare the variable here and assign
        # it in start_listener() later on.
        self._listener_task = None

    def __init_subclass__(cls, **kwargs):
        # While most objects are identified by a human-readable name, at configuration
        # time listeners do not have names as part of their class hence we identify
        # them by their filepaths for errors that arise at configuration time.
        if not hasattr(cls, "listener_type"):
            raise RequiredListenerConfigurationParameterNotDeclaredError(
                listener_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="listener_type",
            )

        if not isinstance(cls.listener_type, BaseListenerType):
            raise ListenerConfigurationParameterTypeError(
                listener_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="listener_type",
                parameter_type="ListenerType",
            )

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.listener_id)})"

    def __repr__(self) -> str:
        return (
            f"Listener(name={self.name!r}, description={self.description!r}"
            f"endpoint={self.endpoint!r}, parameters={self.parameters!r})"
        )

    @abstractmethod
    async def on_listener_started(self) -> None: ...

    @abstractmethod
    async def on_listener_running(self) -> None: ...

    @abstractmethod
    async def on_listener_stopped(self) -> None: ...

    @abstractmethod
    async def on_listener_cancelled(self) -> None: ...

    @abstractmethod
    async def on_listener_errored(self, exception: Exception) -> None: ...

    async def start_listener(self) -> None:
        if self.status.state in (ListenerState.STARTED or ListenerState.RUNNING):
            raise ListenerAlreadyRunningError(
                listener_str=str(self),
                error_message=(
                    "The listener cannot be started because it is already started or "
                    "running."
                ),
            )

        # Clear the signal to the listener to stop running if it is set, so it won't
        # instantly stop.
        self.stop_listener_event.clear()

        # The listener is now started.
        self.status.transition_to_started()
        try:
            await self.on_listener_started()
        # ListenerStartError is raised within on_listener_started() to abort the
        # listener start process if preconditions are not met.
        except ListenerStartError as exc:
            # The listener is now initialized.
            self.status.transition_to_initialized()
            raise ListenerStartFrameworkError(
                listener_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            self.listener_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The listener is now fatally errored.
            self.status.transition_to_fatal(listener=str(self), exception=exc)
            raise exc

        self._listener_task = asyncio.create_task(self._run_listener())

    async def stop_listener(self) -> None:
        if self.status.state != ListenerState.RUNNING:
            raise ListenerNotRunningError(
                listener_str=str(self),
                error_message=(
                    "The listener cannot be stopped because it is not running."
                ),
            )

        try:
            await self.on_listener_stopped()
        # ListenerStopError is raised within on_listener_stopped() to abort the
        # listener stop process if preconditions are not met.
        except ListenerStopError as exc:
            # The listener has not changed from its running state.
            self.status.transition_to_running()
            raise ListenerStopFrameworkError(
                listener_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            )
        except Exception as exc:
            self.listener_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The listener is now fatally errored.
            self.status.transition_to_fatal(listener=str(self), exception=exc)
            raise exc

        # Signal to the listener to stop running.
        self.stop_listener_event.set()

    async def cancel_listener(self) -> None:
        if self.status.state != ListenerState.RUNNING:
            raise ListenerNotRunningError(
                listener_str=str(self),
                error_message=(
                    "The listener cannot be cancelled because it is not running."
                ),
            )

        # Cancel the listener.
        self._listener_task.cancel()

        # Wait for the task to finish. Then remove the task reference.
        while not self._listener_task.done():
            await asyncio.sleep(0.1)
        self._listener_task = None

        try:
            await self.on_listener_cancelled()
        except Exception as exc:
            self.listener_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The listener is now fatally errored.
            self.status.transition_to_fatal(listener=str(self), exception=exc)
            raise exc

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

    async def _run_listener(self):
        try:
            try:
                # The listener is now running.
                self.status.transition_to_running()

                await self.on_listener_running()

                # The listener is now stopped.
                self.status.transition_to_stopped()
                self._listener_task = None
            except asyncio.CancelledError:
                # The listener is now cancelled
                self.status.transition_to_cancelled()
            except ListenerRuntimeError as exc:
                framework_exc = ListenerRuntimeFrameworkError(
                    listener_str=str(self),
                    error_message=exc.message,
                    detail=exc.detail,
                )
                # The listener is now errored.
                self.status.transition_to_errored(exception=framework_exc)
                try:
                    # `on_listener_errored()` should receive the unwrapped 'raw'
                    # exception.
                    await self.on_listener_errored(exception=exc)
                except Exception as exc:
                    self.listener_logger.opt(ansi=True).error(
                        "<bold><red>{}</></>",
                        traceback.format_exc(),
                    )
                    # The listener is now fatally errored.
                    self.status.transition_to_fatal(
                        listener=str(self),
                        exception=exc,
                    )
        except Exception as exc:
            self.listener_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            self.status.transition_to_fatal(listener=str(self), exception=exc)
            # The listener is now fatally errored.
            try:
                await self.on_listener_errored(exc)
            except Exception as exc:
                self.listener_logger.opt(ansi=True).error(
                    "<bold><red>{}</></>",
                    traceback.format_exc(),
                )
                self.status.transition_to_fatal(listener=str(self), exception=exc)
