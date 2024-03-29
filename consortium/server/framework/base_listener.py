import asyncio
import uuid
from abc import ABC, abstractmethod
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
from consortium.server.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
)
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.listener_objects import ListenerState, ListenerStatus


class BaseListener(ABC):
    def __init__(
        self,
        listener_type: ListenerType,
        name: str = "",
        endpoint: str = "",
        options: (
            dict[
                str,
                SingleValueOption
                | ListValueOption
                | ChoiceValueOption
                | DictionaryValueOption,
            ]
            | None
        ) = None,
    ):
        self.listener_id = uuid.uuid4()
        self.name = name
        self.endpoint = endpoint
        self.listener_type = listener_type
        self.options = options
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
        self._task = None

    @abstractmethod
    async def on_listener_started(self) -> None: ...

    @abstractmethod
    async def on_listener_running(self) -> None: ...

    @abstractmethod
    async def on_listener_stopped(self) -> None: ...

    @abstractmethod
    async def on_listener_cancelled(self) -> None: ...

    @abstractmethod
    async def on_listener_errored(self, exc: Exception) -> None: ...

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

                self._task = None
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

    async def start_listener(self):
        if self.status.state == ListenerState.STARTED:
            raise ListenerStartError(detail="Listener is already running")

        # ListenerStartError can be raised here to indicate some sort of validation
        # failure
        self.status.transition_to_started()
        await self.on_listener_started()

        self._task = asyncio.create_task(self._run_listener())

    async def stop_listener(self):
        if self.status.state != ListenerState.RUNNING:
            raise ListenerStopError(detail="Listener is not running")

        await self.on_listener_stopped()

        self.stop_listener_event.set()

    async def cancel_listener(self):
        if self.status.state != ListenerState.RUNNING:
            raise ListenerCancellationError(detail="Listener is not running")
        self._task.cancel()
        self._task = None

    def to_json(self) -> dict[str, Any]:
        return {
            "listener_id": str(self.listener_id),
            "name": self.name,
            "endpoint": self.endpoint,
            "listener_type": self.listener_type.to_json(),
            "options": {
                option_name: {**option.to_json(), "value": option.get_option_value()}
                for option_name, option in self.options.items()
            },
            "status": self.status.to_json(),
            "agent_ids": [str(agent.agent_id) for agent in self.agents.values()],
        }
