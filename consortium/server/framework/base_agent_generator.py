import asyncio
import uuid
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Any

from consortium.server.framework.framework_exceptions import (
    AgentGeneratorBuildError,
    AgentGeneratorCancellationError,
    AgentGeneratorCompletionError,
    AgentGeneratorQueueError,
)
from consortium.server.objects.agent_generator_objects import AgentGeneratorStatus


class BaseAgentGenerator(ABC):
    def __init__(
        self,
        options: dict[str, Any],
    ):
        self.options = options
        # agent generator status is initialized with a state of QUEUED
        self.status = AgentGeneratorStatus()
        self.agent_generator_id = uuid.uuid4()

        # state is used to store any state information that the agent generator may
        # need to store and share amongst its user defined methods
        self.state = SimpleNamespace()

        # hold a reference to the asyncio task to prevent garbage collection
        self._agent_generator_run_task = None

    @abstractmethod
    async def on_agent_generator_queued(self) -> None: ...

    @abstractmethod
    async def on_agent_generator_building(self) -> None: ...

    @abstractmethod
    async def on_agent_generator_completed(self) -> None: ...

    @abstractmethod
    async def on_agent_generator_errored(self, exc: Exception) -> None: ...

    @abstractmethod
    async def on_agent_generator_cancelled(self) -> None: ...

    async def _run_agent_generator(self) -> None:
        # run the on_agent_generator_generate method, if an uncaught exception is
        # raised, the generator is deemed to have failed, after the method has
        # completed, run the on_agent_generator_stop method, if an uncaught exception is
        # raised during the running of that method, the generator is also deemed to have
        # failed
        try:
            try:
                self.status.transition_to_queued()
                await self.on_agent_generator_queued()

                self.status.transition_to_building()
                await self.on_agent_generator_building()

                self.status.transition_to_completed()
                await self.on_agent_generator_completed()
            # this handles the case where the generator is manually cancelled by the
            # user
            except asyncio.CancelledError:
                try:
                    self.status.transition_to_cancelled()
                    await self.on_agent_generator_cancelled()
                except AgentGeneratorCancellationError as exc:
                    self.status.transition_to_errored(exc)
                    await self.on_agent_generator_errored(exc)
            except (
                AgentGeneratorQueueError,
                AgentGeneratorBuildError,
                AgentGeneratorCompletionError,
            ) as exc:
                self.status.transition_to_errored(exc)
                await self.on_agent_generator_errored(exc)
        except Exception as exc:
            self.status.transition_to_fatal(exc)

    async def stop_agent_generator(self) -> None:
        if self.status.state != AgentGeneratorStatus.AgentGeneratorState.BUILDING:
            raise ValueError("Cannot stop agent generator that has not been started.")

        self._agent_generator_run_task.cancel()

    async def start_agent_generator(self) -> None:
        if self.status.state == AgentGeneratorStatus.AgentGeneratorState.BUILDING:
            raise ValueError("Cannot start agent generator that is already running.")

        self._agent_generator_run_task = asyncio.create_task(
            self._run_agent_generator(),
        )

    def to_json(self):
        return {
            "agent_generator_id": str(self.agent_generator_id),
            "status": self.status.to_json(),
            "options": {
                option_name: option.to_json()
                for option_name, option in self.options.items()
            },
        }
