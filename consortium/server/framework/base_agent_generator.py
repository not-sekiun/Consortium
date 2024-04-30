import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from consortium.server.exceptions.agent_generators_api_exceptions import (
    AgentGeneratorAlreadyRunningError,
    AgentGeneratorNotRunningError,
)
from consortium.server.framework.c2_types import AgentType
from consortium.server.framework.exceptions import (
    AgentGeneratorBuildError,
    AgentGeneratorCancellationError,
    AgentGeneratorStartError,
    AgentGeneratorStopError,
)
from consortium.server.objects.agent_generator_objects import (
    AgentGeneratorBuildStepStatus,
    AgentGeneratorState,
    AgentGeneratorStatus,
)


class BaseAgentGeneratorBuildStep(ABC):
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
        self.status = AgentGeneratorBuildStepStatus()

    @abstractmethod
    async def on_agent_generator_build_step_running(
        self,
        stop_agent_generator_event: asyncio.Event,
        parameters: dict,
        build_context: SimpleNamespace,
    ): ...

    async def start_agent_generator_build_step(
        self,
        stop_agent_generator_event: asyncio.Event,
        parameters: dict,
        build_context: SimpleNamespace,
    ):
        self.datetime_started = datetime.now()
        self.status.transition_to_running()
        try:
            await self.on_agent_generator_build_step_running(
                stop_agent_generator_event=stop_agent_generator_event,
                parameters=parameters,
                build_context=build_context,
            )
            self.status.transition_to_completed()
        except AgentGeneratorBuildError as exc:
            self.status.transition_to_errored(exc)
            raise exc
        except Exception as exc:
            self.status.transition_to_fatal(exc)
            raise exc
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
            "status": self.status.to_json(),
        }


class BaseAgentGenerator(ABC):
    def __init__(
        self,
        agent_type: AgentType,
        agent_generator_build_steps: list[BaseAgentGeneratorBuildStep] = None,
        name: str = "",
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.agent_generator_id = uuid.uuid4()
        self.agent_generator_build_steps = (
            agent_generator_build_steps if agent_generator_build_steps else []
        )
        self.name = name
        self.description = description
        self.agent_type = agent_type
        self.parameters = parameters
        self.datetime_created = datetime.now()
        # agent generator status is initialized with a state of QUEUED
        self.status = AgentGeneratorStatus()

        # build_context is used to store any context information that the agent
        # generator may need to store and share amongst its agent generator build steps
        self.build_context = SimpleNamespace()
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
    async def on_agent_generator_started(self) -> None:
        """
        This method is called when the agent generator is started. To prevent the agent
        generator from starting raise the framework exception AgentGeneratorStartError.
        Returning from this method will allow the agent generator to continue starting.

        This method should be used to perform any setup or validation required before
        the agent generator is queued.
        """

    @abstractmethod
    async def on_agent_generator_completed(self) -> None:
        """
        This method is called when the agent generator is completed. Completion occurs
        when the agent generator runs without erroring, stopping, or cancellation.

        This method should be used to perform any cleanup required after the agent
        generator has completed.
        """

    @abstractmethod
    async def on_agent_generator_stopped(self) -> None:
        """
        This method is called when the agent generator is stopped. To prevent the agent
        generator from stopping raise the framework exception AgentGeneratorStopError.
        Returning from this method will allow the agent generator to set the
        self.stop_agent_generator_event asynchronous event flag which will signal to
        the agent generator main runtime loop to stop.

        This method should be used to perform any cleanup required before the agent
        generator is stopped.
        """

    @abstractmethod
    async def on_agent_generator_cancelled(self) -> None:
        """
        This method is called when the agent generator is cancelled. Cancellation
        occurs forcefully without setting the self.stop_agent_generator_event
        asynchronous event flag. To prevent the agent generator from being cancelled
        raise the framework exception AgentGeneratorCancellationError. Returning from
        this method will allow the agent generator to be cancelled.

        This method should be used to perform any cleanup required before the agent
        generator is forcefully cancelled.
        """

    @abstractmethod
    async def on_agent_generator_errored(self, exc: Exception) -> None:
        """
        This method is called when any unhandled exception is raised within the agent
        generator. This excludes framework exceptions like AgentGeneratorStartError,
        AgentGeneratorStopError, AgentGeneratorRuntimeError, and
        AgentGeneratorCancellationError as well as asyncio.CancelledError which is
        raised when cancelling the agent generator.
        """

    async def _run_agent_generator(self) -> None:
        try:
            try:
                # The agent generator is now building.
                self.status.transition_to_building()
                for agent_generator_build_step in self.agent_generator_build_steps:
                    await agent_generator_build_step.start_agent_generator_build_step(
                        stop_agent_generator_event=self.stop_agent_generator_event,
                        parameters=self.parameters,
                        build_context=self.build_context,
                    )
                    if self.stop_agent_generator_event.is_set():
                        break

                # Returning from on_agent_generator_building() occurs either when it
                # completes or is signalled to stop.
                if self.stop_agent_generator_event.is_set():
                    # The agent generator is now stopped.
                    self.status.transition_to_stopped()
                    self._agent_generator_task = None
                    return

                # The agent generator is now completed.
                self.status.transition_to_completed()
                await self.on_agent_generator_completed()
            except asyncio.CancelledError:
                self.status.transition_to_cancelled()
            except AgentGeneratorBuildError as exc:
                # The agent generator is now errored.
                self.status.transition_to_errored(exc)
                try:
                    await self.on_agent_generator_errored(exc)
                except Exception as exc:
                    # The agent generator is now fatally errored.
                    self.status.transition_to_fatal(exc)
        except Exception as exc:
            # The agent generator is now fatally errored.
            self.status.transition_to_fatal(exc)
            try:
                await self.on_agent_generator_errored(exc)
            except Exception as exc:
                self.status.transition_to_fatal(exc)

    async def start_agent_generator(self) -> None:
        if self.status.state == AgentGeneratorState.RUNNING:
            raise AgentGeneratorAlreadyRunningError(
                message=(
                    "The agent generator cannot be started because it is already "
                    "building an agent."
                ),
            )

        # The agent generator is now started.
        self.status.transition_to_started()
        try:
            await self.on_agent_generator_started()
        except AgentGeneratorStartError as exc:
            # The agent generator is now initialized.
            self.status.transition_to_initialized()
            raise exc

        self._agent_generator_task = asyncio.create_task(self._run_agent_generator())

    async def stop_agent_generator(self) -> None:
        if self.status.state != AgentGeneratorState.RUNNING:
            raise AgentGeneratorNotRunningError(
                message=(
                    "The agent generator cannot be stopped because it is not building "
                    "an agent."
                ),
            )

        try:
            await self.on_agent_generator_stopped()
        except AgentGeneratorStopError as exc:
            # The agent generator has not changed from its building state.
            self.status.transition_to_building()
            raise exc

        # Signal to the agent generator runtime to stop.
        self.stop_agent_generator_event.set()

    async def cancel_agent_generator(self) -> None:
        if self.status.state != AgentGeneratorState.RUNNING:
            raise AgentGeneratorNotRunningError(
                message=(
                    "The agent generator cannot be cancelled because it is not "
                    "building an agent."
                ),
            )

        try:
            await self.on_agent_generator_cancelled()
        except AgentGeneratorCancellationError as exc:
            self.status.transition_to_building()
            raise exc

        # Cancel the agent generator.
        self._agent_generator_task.cancel()
        self._agent_generator_task = None

    def to_json(self):
        return {
            "agent_generator_id": str(self.agent_generator_id),
            "agent_generator_build_steps": [
                agent_generator_build_step.to_json()
                for agent_generator_build_step in self.agent_generator_build_steps
            ],
            "name": self.name,
            "description": self.description,
            "status": self.status.to_json(),
            "agent_type": self.agent_type.to_json(),
            "parameters": self.parameters,
            "datetime_created": self.datetime_created.isoformat(),
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.agent_generator_id)})'

    def __repr__(self) -> str:
        return (
            f"AgentGenerator(agent_type={self.agent_type!r}, name={self.name!r}, "
            f"parameters={self.parameters!r})"
        )
