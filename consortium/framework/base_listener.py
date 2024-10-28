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
    """
    A class that allows listeners to manage the lifetime of an agent from registration
    to checking in to deregistration, as well as to manage access to agents registered
    locally to the specific listener. This class is not meant to be directly imported
    and used, rather it is used from within the
    [BaseListener][consortium.framework.base_listener.BaseListener] class.
    """

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
        hostname: str | None = None,
        agent_data: dict[str, Any] | None = None,
    ) -> Agent:
        """
        Register a new connected agent with the listener.

        Args:
            agent_type (BaseAgentType): The agent type of the agent to be registered.
            name (str): The human-readable name of the agent.
            description (str): A description of the agent.
            endpoint (str): A human-readable representation of the network endpoint that
                uniquely identifies the agent. This is typically the socket address of
                the agent.
            is_admin (bool | None): A boolean that indicates whether the agent is
                running with administrator/superuser privileges.
            os (str | None): The operating system of the agent.
            version (str | None): The version of the operating system that the agent is
                running on.
            arch (str | None): The architecture of the system that the agent is running
                on.
            pid (int | None): The process ID of the agent.
            locale (str | None): The locale of the system that the agent is running on.
            remote_host_address (str | None): The remote host address of the agent.
            local_host_address (str | None): The local host address of the agent.
            hostname (str | None): The hostname of the system that the agent is running
                on.
            agent_data (dict[str, Any] | None): A dictionary of any additional data that
                the agent may send to the listener.

        Returns:
            Agent: An object representing the agent that was registered.
        """

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
            hostname=hostname,
            agent_data=agent_data,
        )
        self._agents[str(agent.agent_id)] = agent
        return agent

    async def check_in_connected_agent_by_agent_id(self, agent_id: str) -> None:
        """
        Check in a connected agent by its agent ID. This method simply updates the last
        check-in time of the agent to indicate that the agent is still connected and
        has called back.

        Args:
            agent_id (str): The agent ID of the agent to check in. This should be a
                UUID4 string.

        Raises:
            ListenerSpecificAgentNotFoundError: Raised if the agent with the specified
                agent ID is not found.

        Returns:
            None
        """

        if agent_id not in self._agents:
            raise ListenerSpecificAgentNotFoundError
        await self._agents_service.check_in_agent_by_agent_id(agent_id=agent_id)

    async def deregister_connected_agent_by_agent_id(self, agent_id: str) -> None:
        """
        Deregister a connected agent by its agent ID. This method removes the agent from
        the listener's list of connected agents and also removes the agent from the
        database. This effectively marks an agent as disconnected.

        Args:
            agent_id (str): The agent ID of the agent to deregister. This should be a
                UUID4 string.

        Raises:
            ListenerSpecificAgentNotFoundError: Raised if the agent with the specified
                agent ID is not found.

        Returns:
            None
        """

        if agent_id not in self._agents:
            raise ListenerSpecificAgentNotFoundError
        await self._agents_service.remove_agent_by_agent_id(agent_id=agent_id)
        self._agents.pop(str(agent_id))

    def get_all_connected_agents(self) -> list[Agent]:
        """
        Get all connected agents that are registered with the specific listener that is
        using this agent manager.

        Returns:
            list[Agent]: A list of all connected agents that are registered with the
                specific listener that is using this agent manager.
        """

        return list(self._agents.values())

    def get_connected_agent_by_agent_id(self, agent_id: str) -> Agent:
        """
        Get a connected agent by its agent ID for the specific listener that is using
        this agent manager.

        Args:
            agent_id (str): The agent ID of the agent to get. This should be a UUID4
                string.

        Raises:
            ListenerSpecificAgentNotFoundError: Raised if the agent with the specified

        Returns:
            Agent: The agent with the specified agent ID.
        """

        try:
            return self._agents[agent_id]
        except KeyError:
            raise ListenerSpecificAgentNotFoundError


class BaseListener(ABC):
    """
    The Abstract Base Class for creating listeners. Any listener that is to be used in
    the Consortium framework must inherit from this class and implement all of its
    abstract methods. The listener is responsible for managing the lifecycle of agents,
    which include: registration/de-registration, check-ins, sending tasks, and receiving
    results.

    Attributes:
        listener_id (uuid.UUID): A UUID4 object which serves to act as a unique
            identifier for the listener. The listener ID serves as the primary
            identifier of the listener.
        name (str): The human-readable name of the listener. Note that the listener's
            name is not used to identify it and hence can be non-unique.
        description (str): A description of the listener.
        endpoint (str): A human-readable representation of the network endpoint that
            uniquely identifies the listener. This is typically the socket address of
            the listener.
        listener_type: The listener type that the listener is associated with.
        parameters (dict[str, Any] | None): A dictionary of parameters that the listener
            may need for its operation. The available parameters that parameterize the
            listener are defined in the listener's listener template, which is tied to
            the listener by its listener type.
        status (ListenerStatus): The status of the listener, which includes both the
            state of the listener and any exception information as well if the listener
            has errored.
        datetime_created (datetime.datetime): The date and time that the listener was
            created, or more specifically instantiated.
        environment (types.SimpleNamespace): A namespace object that allows the
            listener to store any variables that it wants without potentially clashing
            with other variables in the listener. This is useful for sharing variables
            between the listener's user-defined methods.
        stop_listener_event (asyncio.Event): An asyncio event object that is used to
            signal to the listener runtime loop to exit gracefully. The implementation
            of the listener runtime loop should either check this event periodically or
            specifically block on it and exit once it is set.
        agents_manager (consortium.framework.base_listener._AgentsManager): A class that
            allows listeners to manage the lifetime of an agent from registration to
            checking in to deregistration, as well as to manage access to agents
            registered locally to the specific listener.
    """

    listener_type: BaseListenerType

    def __init__(
        self,
        name: str = "",
        description: str = "",
        endpoint: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """
        The constructor method for the `BaseListener` class. This method creates a
        listener and is primarily parameterized by the `parameters` dictionary
        parameter. While the constructor can be called directly, it is recommended to
        create listeners  through their associated listener templates.

        Args:
            name (str): The human-readable name of the listener.
            description (str): A description of the listener.
            endpoint (str): A human-readable representation of the network endpoint
                that uniquely identifies the listener. This is typically the socket
                address of the listener.
            parameters (dict[str, Any] | None): A dictionary of parameters that the
                listener may need for its operation. The available parameters that
                parameterize the listener are defined in the listener's listener
                template, which is tied to the listener by its listener type.
        """
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
    async def on_listener_started(self) -> None:
        """
        This method is called when the listener is started. This method is called after
        the listener has been initialized and before the listener is running. This
        method is intended to be overridden by the user to perform any setup that is
        required before the listener starts running. If the listener is not ready to
        start - typically failing some precondition - the user can raise a
        `ListenerStartError` to abort the listener start process.

        Returns:
            None

        Raises:
            ListenerStartError: An error that is manually raised by the user to abort
                the listener start process if preconditions are not met.

        Example:
            ```python
            async def on_listener_started(self) -> None:
                # `self.parameters` is the dictionary of parameters passed into the
                # listener from the constructor.
                local_host = self.parameters["local_host"]
                local_port = self.parameters["local_port"]

                # Try creating a socket to check if the listener can bind to the
                # provided host and port.
                try:
                    test_socket = socket.socket()
                    test_socket.bind((local_host, local_port))
                    test_socket.close()
                except socket.error as exc:
                    # Raise a ListenerStartError if the listener is unable to bind to
                    # the provided host and port. This signals to the framework that
                    # some sort of intentional validation failed as opposed to an
                    # unhandled exception.
                    raise ListenerStartError(
                        f"An error occurred while attempting to start the listener. "
                        f"Listener was unable to bind to the provided host and port due "
                        f"to the following socket error: {exc}",
                    )
            ```
        """

    @abstractmethod
    async def on_listener_running(self) -> None:
        """
        This method is the main runtime loop of the listener. This method is called
        only after the listener has been started and its `on_listener_started` has run
        to completion without raising `ListenerStartError`. This method is intended to
        be overridden by the user to implement the listener's runtime logic. To
        communicate to the framework that the listener has encountered some runtime
        error, the user can raise a `ListenerRuntimeError`.

        This method is expected to run indefinitely until the listener is stopped and is
        responsible for managing the lifecycle of agents, which include:
        registration/deregistration, check-ins, sending tasks, and receiving results.
        The runtime loop is expected to periodically check the `stop_listener_event` to
        determine if it should exit.

        Returns:
            None

        Raises:
            ListenerRuntimeError: An error that is manually raised by the user to
                communicate that the listener has encountered some runtime error. This
                will automatically be caught and change the listener's status's state
                to `ERRORED` as opposed to `FATAL` which is reserved for unhandled
                exceptions.

        Example:
            ```python
            async def _handle_agent(self, reader, writer) -> None:
                # On first callback, we need to register the agent to the agents
                # service to make the agent available to the rest of the framework. We
                # do this through the listener's own agents manager.
                raw_data = await reader.read(1024 * 1024)
                agent_data = json.loads(data.decode())
                self.agents_manage.register_new_connected_agent(**agent_data)
                while True:
                    # On each subsequent callback we need to update the framework that
                    # the agent has checked in.
                    raw_data = await reader.read(1024 * 1024)
                    agent_data = json.loads(data.decode())

            # Simple TCP socket server that listens for callbacks from agents.
            async def _listen_for_socket_connections(self):
                local_host = self.parameters["local_host"]
                local_port = self.parameters["local_port"]

                server = await asyncio.start_server(
                    client_connected_cb=self._handle_client_connection,
                    host=local_host,
                    port=local_port,
                )

                async with server:
                    await server.serve_forever()

            async def on_listener_running(self):
                while True:
                    if self.stop_listener_event.is_set():
                        break
            ```
        """

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
