import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from consortium.server.framework.framework_exceptions import (
    AgentGeneratorBuildError,
    AgentGeneratorCancellationError,
    AgentGeneratorQueueError,
    AgentGeneratorStopError,
)
from consortium.server.framework.framework_types import AgentType
from consortium.server.objects.agent_generator_objects import (
    AgentGeneratorState,
    AgentGeneratorStatus,
)
from consortium.server.server_exceptions import (
    AgentGeneratorAlreadyBuildingError,
    AgentGeneratorNotBuildingError,
)


class AgentGeneratorBuildStep(ABC):
    def __init__(
        self,
        name: str = "",
        description: str = "",
        ignore_failure: bool = False,
    ):
        self.agent_generator_build_step_id = uuid.uuid4()
        self.name = name
        self.description = description
        self.ignore_failure = ignore_failure
        self.datetime_started = None
        self.datetime_stopped = None
        self.status = None

    @abstractmethod
    async def on_agent_generator_build_step_running(self, build_context: dict): ...

    async def start_agent_generator_build_step(self, build_context: dict):
        self.datetime_started = datetime.now()
        try:
            await self.on_agent_generator_build_step_running(
                build_context=build_context,
            )
        except Exception as exc:
            # TODO: Change status here
            print(exc)
        except AgentGeneratorBuildError as exc:
            # TODO: Change status here
            print(exc)
        finally:
            self.datetime_stopped = datetime.now()

    def to_json(self) -> dict[str, Any]:
        return {
            "agent_generator_build_step_id": str(self.agent_generator_build_step_id),
            "name": self.name,
            "description": self.description,
            "ignore_failure": self.ignore_failure,
            "datetime_started": self.datetime_started.isoformat()
            if self.datetime_started
            else None,
            "datetime_stopped": self.datetime_stopped.isoformat()
            if self.datetime_stopped
            else None,
            "time_elapsed_in_seconds": (
                self.datetime_stopped - self.datetime_started
            ).seconds
            if self.datetime_started and self.datetime_stopped
            else None,
        }


# TODO: Add analogous error handling to base_listener. Add AgentGeneratorBuildSteps
class BaseAgentGenerator(ABC):
    def __init__(
        self,
        agent_type: AgentType,
        name: str = "",
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.agent_generator_id = uuid.uuid4()
        self.name = name
        self.description = description
        self.agent_type = agent_type
        self.parameters = parameters
        # agent generator status is initialized with a state of QUEUED
        self.status = AgentGeneratorStatus()

        # state is used to store any state information that the agent generator may
        # need to store and share amongst its user defined methods
        self.state = SimpleNamespace()
        # self.stop_agent_generator_event is used to signal to the agent generator
        # runtime to exit.
        self.stop_agent_generator_event = asyncio.Event()

        # asyncio type tasks are held by a weak reference by default, so they can be
        # garbage collected at any time mid-execution, to prevent this we have to store
        # a reference of the task in a variable. We declare the variable here and assign
        # it in start_agent_generator() later on
        self._agent_generator_task = None

    @abstractmethod
    async def on_agent_generator_queued(self) -> None:
        """
        This method is called when the agent generator is queued to be run. This method
        should be used to perform any setup or checks that are required before the
        agent generator is started. This method should raise a AgentGeneratorQueueError
        if the agent generator cannot be queued failing a precondition.
        """

    @abstractmethod
    async def on_agent_generator_building(self) -> None:
        """
        This method is called when the agent generator is building. The build process is
        blocking but not indefinite. This method should raise a AgentGeneratorBuildError
        if the agent generator cannot be built.
        """

    @abstractmethod
    async def on_agent_generator_completed(self) -> None:
        """
        This method is called when the agent generator has completed. A completed agent
        generator is one which has run to completion without ever being stopped or
        cancelled. This method should be used to perform any cleanup or checks that are
        required after the agent generator has completed.
        """

    @abstractmethod
    async def on_agent_generator_stopped(self) -> None:
        """ """

    @abstractmethod
    async def on_agent_generator_cancelled(self) -> None:
        """
        This method is called when the agent generator is either stopped or cancelled
        where the agent generator never runs to completion. Stopping will set the
        self.stop_agent_generator_event asynchronous event flag, while cancelling will
        raise an asyncio.CancelledError to more forcefully stop the agent generator.
        This method should raise an AgentGeneratorCancellationError if the agent
        generator cannot be stopped or cancelled.
        """

    @abstractmethod
    async def on_agent_generator_errored(self, exc: Exception) -> None:
        """
        This method is called when the agent generator encounters an unexpected error
        while running. If any error apart from AgentGeneratorQueueError,
        AgentGeneratorBuildError, AgentGeneratorStopError,
        AgentGeneratorCancellationError is raised, this method is called.
        """

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

                if self.stop_agent_generator_event.is_set():
                    # Reduce code duplication by raising a CancelledError to move to
                    # the cancelled state which is reached when attempting to stop or
                    # cancel the agent generator. Stopping is simply a more graceful
                    # way of cancelling the agent generator.
                    raise asyncio.CancelledError

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
                AgentGeneratorStopError,
            ) as exc:
                self.status.transition_to_errored(exc)
                await self.on_agent_generator_errored(exc)
        except Exception as exc:
            self.status.transition_to_fatal(exc)

    async def start_agent_generator(self) -> None:
        if self.status.state == AgentGeneratorState.BUILDING:
            raise AgentGeneratorAlreadyBuildingError(
                message=(
                    "The agent generator cannot be started because it is already "
                    "building an agent."
                ),
            )

        self._agent_generator_task = asyncio.create_task(
            self._run_agent_generator(),
        )

    async def stop_agent_generator(self) -> None:
        if self.status.state != AgentGeneratorState.BUILDING:
            raise AgentGeneratorNotBuildingError(
                message=(
                    "The agent generator cannot be stopped because it is not building "
                    "an agent."
                ),
            )

        self.stop_agent_generator_event.set()

    async def cancel_agent_generator(self) -> None:
        if self.status.state != AgentGeneratorState.BUILDING:
            raise AgentGeneratorNotBuildingError(
                message=(
                    "The agent generator cannot be cancelled because it is not "
                    "building an agent."
                ),
            )

        self._agent_generator_task.cancel()
        self._agent_generator_task = None

    def to_json(self):
        return {
            "agent_generator_id": str(self.agent_generator_id),
            "name": self.name,
            "description": self.description,
            "status": self.status.to_json(),
            "agent_type": self.agent_type.to_json(),
            "parameters": self.parameters,
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.agent_generator_id)})'

    def __repr__(self) -> str:
        return (
            f"AgentGenerator(agent_type={self.agent_type!r}, name={self.name!r}, "
            f"parameters={self.parameters!r})"
        )
