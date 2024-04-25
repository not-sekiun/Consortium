import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.framework.framework_exceptions import (
    ListenerCancellationError,
    ListenerRuntimeError,
    ListenerStartError,
    ListenerStopError,
)
from consortium.server.framework.framework_types import ListenerType
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.listener_objects import ListenerState, ListenerStatus
from consortium.server.server_exceptions import (
    ListenerAlreadyRunningError,
    ListenerNotRunningError,
)


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

        # asyncio type tasks are held by a weak reference by default, so they can be
        # garbage collected at any time mid-execution, to prevent this we have to store
        # a reference of the task in a variable. We declare the variable here and assign
        # it in start_listener() later on
        self._listener_task = None

    @abstractmethod
    async def on_listener_started(self) -> None:
        """
        This method is called when the listener is started. This method should be used
        to perform any setup or checks that are required before the listener is
        started. This method should raise a ListenerStartError if the listener cannot be
        started.
        """

    @abstractmethod
    async def on_listener_running(self) -> None:
        """
        This method is called to run the listener. This method should be used to perform
        any actions that are required while the listener is running and should be a
        blocking coroutine that has some mechanism in place to check if the
        self.stop_listener_event asynchronous event flag is set to know when to stop
        running. This method should raise a ListenerRuntimeError if the  listener
        encounters an error while running.
        """

    @abstractmethod
    async def on_listener_stopped(self) -> None:
        """
        This method is called when the listener is stopped. This method should be used
        to perform any cleanup or actions that are required before the listener is
        stopped such as gracefully disconnecting any agents or releasing any held
        resources. This method should raise a ListenerStopError if the listener cannot
        be stopped.
        """

    @abstractmethod
    async def on_listener_cancelled(self) -> None:
        """
        This method is called when the listener is cancelled forcefully without setting
        the self.stop_listener_event asynchronous event flag. This method should be used
        to perform any cleanup or actions that are required before the listener is
        cancelled such as gracefully disconnecting any agents or releasing any held
        resources. This method should raise a ListenerCancellationError if the listener
        cannot be cancelled.
        """

    @abstractmethod
    async def on_listener_errored(self, exc: Exception) -> None:
        """
        This method is called when the listener encounters an unexpected error while
        running. If any error apart from ListenerStartError, ListenerStopError,
        ListenerCancellationError or ListenerRuntimeError is raised, this method is
        called.
        """

    # To avoid exposing the internal workings of the AgentsService service to the
    # implementer we instead provide a create_agent() method that can be used to create
    # a new agent in the publicly exposed framework.
    @staticmethod
    def create_agent() -> Agent:
        return server_singletons.agents_service.create_agent()

    async def _run_listener(self):
        try:
            try:
                self.status.transition_to_running()
                await self.on_listener_running()

                self.status.transition_to_stopped()
                await self.on_listener_stopped()

                self._listener_task = None
            except asyncio.CancelledError:
                try:
                    self.status.transition_to_cancelled()
                    await self.on_listener_cancelled()
                except ListenerCancellationError as exc:
                    self.status.transition_to_errored(exc)
            except (ListenerStartError, ListenerRuntimeError, ListenerStopError) as exc:
                self.status.transition_to_errored(exc)
                await self.on_listener_errored(exc)
        except Exception as exc:
            self.status.transition_to_fatal(exc)

    async def start_listener(self) -> None:
        if self.status.state == ListenerState.STARTED:
            raise ListenerAlreadyRunningError(
                message="The listener cannot be started because it is already running",
            )

        # ListenerStartError is raised within on_listener_started() to abort the
        # listener start process if preconditions are not met.
        self.status.transition_to_started()
        try:
            await self.on_listener_started()
        except ListenerStartError as exc:
            self.status.transition_to_errored(exception=exc)
            raise exc

        self._listener_task = asyncio.create_task(self._run_listener())

    async def stop_listener(self) -> None:
        if self.status.state != ListenerState.RUNNING:
            raise ListenerNotRunningError(
                message="The listener cannot be stopped because it is not running.",
            )

        try:
            self.stop_listener_event.set()
        except ListenerStopError as exc:
            self.status.transition_to_running()
            self.stop_listener_event.clear()
            raise exc

    async def cancel_listener(self) -> None:
        if self.status.state != ListenerState.RUNNING:
            raise ListenerNotRunningError(
                message="The listener cannot be cancelled because it is not running.",
            )
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
