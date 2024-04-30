import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.listeners_api_exceptions import (
    ListenerAlreadyRunningError,
    ListenerNotRunningError,
)
from consortium.server.framework.c2_types import ListenerType
from consortium.server.framework.exceptions import (
    ListenerCancellationError,
    ListenerRuntimeError,
    ListenerStartError,
    ListenerStopError,
)
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.listener_objects import ListenerState, ListenerStatus


class BaseListener(ABC):
    def __init__(
        self,
        listener_type: ListenerType,
        name: str = "",
        description: str = "",
        endpoint: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.listener_id = uuid.uuid4()
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.listener_type = listener_type
        self.parameters = parameters
        self.datetime_created = datetime.now()
        # Original status.state is set to STOPPED.
        self.status = ListenerStatus()

        # self.state is used to store any state information that the listener may need
        # to store and share amongst its user defined methods.
        self.state = SimpleNamespace()
        # self.stop_listener_event used to signal to the listener runtime loop to exit.
        # The implementation of the listener runtime loop should check this event
        # periodically and exit if it is set.
        self.stop_listener_event = asyncio.Event()
        # self.agents is a local storage of agents that have registered with this
        # listener for access within the listener.
        self.agents = {}
        # self.listener_logger is an internal logger to use for logging within the
        # listener to standard output and log files.
        self.listener_logger = logger.bind(
            logger_name=f'Consortium Listener "{self.name}" ({self.listener_id})',
        )

        # Asyncio type tasks are held by a weak reference by default, so they can be
        # garbage collected at any time mid-execution, to prevent this we have to store
        # a reference of the task in a variable. We declare the variable here and assign
        # it in start_listener() later on.
        self._listener_task = None

    @abstractmethod
    async def on_listener_started(self) -> None:
        """
        This method is called when the listener is started. To prevent the listener
        from starting raise the framework error ListenerStartError. Returning from this
        method will allow the listener to continue starting.

        This method should be used to perform any setup or validation required before
        the listener is started.
        """

    @abstractmethod
    async def on_listener_running(self) -> None:
        """
        This method is called as the listener's main runtime loop. To indicate that an
        error has occurred within this method raise the framework exception
        ListenerRuntimeError. Returning from this method will allow the listener to
        stop running. To detect when the listener should stop running check the
        self.stop_listener_event asynchronous event flag.

        This method should be used to perform the main runtime logic of the listener.
        This includes listening for incoming connections, registering agents, sending
        tasks to and receiving results from agents.
        """

    @abstractmethod
    async def on_listener_stopped(self) -> None:
        """
        This method is called when the listener is stopped. To prevent the listener
        from stopping raise the framework exception ListenerStopError. Returning from
        this method will allow the listener to set the self.stop_listener_event
        asynchronous event flag which will signal to the listener's main runtime loop
        to stop.

        This method should be used to perform any cleanup required before the listener
        is stopped.
        """

    @abstractmethod
    async def on_listener_cancelled(self) -> None:
        """
        This method is called when the listener is cancelled. Cancellation occurs
        forcefully without setting the self.stop_listener_event asynchronous event
        flag. To prevent the listener from being cancelled raise the framework
        exception ListenerCancellationError. Returning from this method will allow the
        listener to be cancelled.

        This method should be used to perform any cleanup required before the listener
        is forcefully cancelled.
        """

    @abstractmethod
    async def on_listener_errored(self, exc: Exception) -> None:
        """
        This method is called when any unhandled exception or the framework exception
        ListenerRuntimeError is raised within the listener's main runtime loop. This
        excludes the exception asyncio.CancelledError which is raised when cancelling
        the listener.
        """

    # To avoid exposing the internal workings of the AgentsService service to the
    # implementer we instead provide a create_agent() method that can be used to create
    # a new agent in the publicly exposed framework.
    def create_agent(self) -> Agent:
        agent = server_singletons.agents_service.create_agent()
        self.agents[agent.agent_id] = agent
        return agent

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
                # The listener is now errored
                self.status.transition_to_errored(exc)
                try:
                    await self.on_listener_errored(exc)
                except Exception as exc:
                    # The listener is now fatally errored.
                    self.status.transition_to_fatal(exc)
        except Exception as exc:
            self.status.transition_to_fatal(exc)
            # The listener is now fatally errored.
            try:
                await self.on_listener_errored(exc)
            except Exception as exc:
                self.status.transition_to_fatal(exc)

    async def start_listener(self) -> None:
        if self.status.state == ListenerState.STARTED:
            raise ListenerAlreadyRunningError(
                message="The listener cannot be started because it is already running",
            )

        # The listener is now started.
        self.status.transition_to_started()
        try:
            await self.on_listener_started()
        # ListenerStartError is raised within on_listener_started() to abort the
        # listener start process if preconditions are not met.
        except ListenerStartError as exc:
            # The listener is now initialized.
            self.status.transition_to_initialized()
            raise exc

        self._listener_task = asyncio.create_task(self._run_listener())

    async def stop_listener(self) -> None:
        if self.status.state != ListenerState.RUNNING:
            raise ListenerNotRunningError(
                message="The listener cannot be stopped because it is not running.",
            )

        try:
            await self.on_listener_stopped()
        # ListenerStopError is raised within on_listener_stopped() to abort the
        # listener stop process if preconditions are not met.
        except ListenerStopError as exc:
            # The listener has not changed from its running state.
            self.status.transition_to_running()
            raise exc

        # Signal to the listener to stop running.
        self.stop_listener_event.set()

    async def cancel_listener(self) -> None:
        if self.status.state != ListenerState.RUNNING:
            raise ListenerNotRunningError(
                message="The listener cannot be cancelled because it is not running.",
            )

        try:
            await self.on_listener_cancelled()
        # ListenerCancellationError is raised within on_listener_cancelled() to abort
        # the listener cancellation process if preconditions are not met.
        except ListenerCancellationError as exc:
            self.status.transition_to_running()
            raise exc

        # Cancel the listener.
        self._listener_task.cancel()
        self._listener_task = None

    def to_json(self) -> dict[str, Any]:
        return {
            "listener_id": str(self.listener_id),
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "listener_type": self.listener_type.to_json(),
            "parameters": self.parameters,
            "status": self.status.to_json(),
            "agent_ids": [str(agent.agent_id) for agent in self.agents.values()],
            "datetime_created": self.datetime_created.isoformat(),
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.listener_id)})'

    def __repr__(self) -> str:
        return (
            f"Listener(listener_type={self.listener_type!r}, name={self.name!r}, "
            f"endpoint={self.endpoint!r}, parameters={self.parameters!r})"
        )
