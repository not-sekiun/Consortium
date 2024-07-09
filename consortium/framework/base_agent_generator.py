import asyncio
import inspect
import json
import sys
import traceback
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from loguru import logger

from consortium.framework.c2_types import AgentType
from consortium.framework.exceptions.agents_framework_exceptions import (
    AgentGeneratorBuildError,
    AgentGeneratorStartError,
    AgentGeneratorStopError,
)
from consortium.server.exceptions.framework_exceptions.agent_generators_framework_exceptions import (
    AgentGeneratorAlreadyRunningError,
    AgentGeneratorBuildError as AgentGeneratorBuildFrameworkError,
    AgentGeneratorBuildStepConfigurationParameterTypeError,
    AgentGeneratorConfigurationParameterTypeError,
    AgentGeneratorCreationParameterTypeError,
    AgentGeneratorNotRunningError,
    AgentGeneratorStartError as AgentGeneratorStartFrameworkError,
    AgentGeneratorStopError as AgentGeneratorStopFrameworkError,
    EmptyAgentGeneratorBuildStepNameError,
    EmptyAgentGeneratorNameError,
    RequiredAgentGeneratorBuildStepConfigurationParameterNotDeclaredError,
    RequiredAgentGeneratorConfigurationParameterNotDeclaredError,
)
from consortium.server.objects.agent_generator_objects import (
    AgentGeneratorBuildStepStatus,
    AgentGeneratorState,
    AgentGeneratorStatus,
)


class BaseAgentGeneratorBuildStep(ABC):
    name: str
    description: str = ""
    ignore_failure: bool = False

    def __init__(self):
        self.agent_generator_build_step_id = uuid.uuid4()
        self.datetime_started = None
        self.datetime_stopped = None
        self.status = AgentGeneratorBuildStepStatus()

        self.working_directory = Path(inspect.getsourcefile(self.__class__)).parent

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "name"):
            raise RequiredAgentGeneratorBuildStepConfigurationParameterNotDeclaredError(
                parameter_name="name",
                agent_generator_build_step_name=sys.modules[cls.__module__].__file__,
            )
        if not isinstance(cls.name, str):
            raise AgentGeneratorBuildStepConfigurationParameterTypeError(
                agent_generator_build_step_name=sys.modules[cls.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not cls.name:
            raise EmptyAgentGeneratorBuildStepNameError(
                agent_generator_build_step_filepath=sys.modules[
                    cls.__module__
                ].__file__,
            )

        if not isinstance(cls.description, str):
            raise AgentGeneratorBuildStepConfigurationParameterTypeError(
                agent_generator_build_step_name=cls.name,
                parameter_name="description",
                parameter_type="str",
            )

        if not isinstance(cls.ignore_failure, bool):
            raise AgentGeneratorBuildStepConfigurationParameterTypeError(
                agent_generator_build_step_name=cls.name,
                parameter_name="ignore_failure",
                parameter_type="bool",
            )

    def __str__(self) -> str:
        return f"{self.name} ({str(self.agent_generator_build_step_id)})"

    def __repr__(self) -> str:
        return (
            f"AgentGeneratorBuildStep(name={self.name!r}, "
            f"description={self.description!r}, ignore_failure={self.ignore_failure})"
        )

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
            self.status.transition_to_errored(exception=exc)
            raise exc
        except Exception as exc:
            self.status.transition_to_fatal(
                agent_generator_build_step_identifier=str(self),
                exception=exc,
            )
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
    agent_type: AgentType
    agent_generator_build_steps: list[BaseAgentGeneratorBuildStep] = (None,)

    def __init__(
        self,
        name: str = "",
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        if parameters is None:
            parameters = {}

        if not isinstance(name, str):
            # The agent generator is identified by its name, but at this point we are
            # still validating the name parameter, so we refer to it by its filepath
            # for now.
            raise AgentGeneratorCreationParameterTypeError(
                agent_generator_str=sys.modules[self.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not name:
            raise EmptyAgentGeneratorNameError(
                agent_generator_filepath=sys.modules[self.__module__].__file__,
            )
        # From here onwards we can refer to the agent generator by its assigned name.
        if not isinstance(description, str):
            raise AgentGeneratorCreationParameterTypeError(
                agent_generator_str=sys.modules[self.__module__].__file__,
                parameter_name="description",
                parameter_type="str",
            )
        try:
            json.dumps(parameters)
        except json.JSONDecodeError:
            raise AgentGeneratorCreationParameterTypeError(
                agent_generator_str=name,
                error_message=(
                    "The parameter 'parameters' must be a dictionary with string keys "
                    "and values that are either: str, int, float, bool, None, lists of "
                    "these types, or nested dictionaries of the same structure to "
                    "ensure JSON serializability."
                ),
            )

        self.name = name
        self.description = description
        self.parameters = parameters

        self.agent_generator_id = uuid.uuid4()
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
        self.agent_generator_logger = logger.bind(
            logger_name=f"Consortium Agent Generator {self}",
        )

        # asyncio type tasks are held by a weak reference by default, so they can be
        # garbage collected at any time mid-execution, to prevent this we have to store
        # a reference of the task in a variable. We declare the variable here and assign
        # it in start_agent_generator() later on
        self._agent_generator_task = None

    def __init_subclass__(cls, **kwargs):
        if cls.agent_generator_build_steps is None:
            cls.agent_generator_build_steps = []

        if not hasattr(cls, "agent_type"):
            raise RequiredAgentGeneratorConfigurationParameterNotDeclaredError(
                parameter_name="agent_type",
                agent_generator_filepath=sys.modules[cls.__module__].__file__,
            )
        if not isinstance(cls.agent_type, AgentType):
            raise AgentGeneratorConfigurationParameterTypeError(
                agent_generator_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="agent_type",
                parameter_type="AgentType",
            )

        if not hasattr(cls, "agent_generator_build_steps"):
            raise RequiredAgentGeneratorConfigurationParameterNotDeclaredError(
                parameter_name="agent_generator_build_steps",
                agent_generator_filepath=sys.modules[cls.__module__].__file__,
            )
        if not isinstance(cls.agent_generator_build_steps, list):
            raise AgentGeneratorConfigurationParameterTypeError(
                agent_generator_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="agent_generator_build_steps",
                parameter_type="list",
            )
        for agent_generator_build_step in cls.agent_generator_build_steps:
            if not isinstance(agent_generator_build_step, BaseAgentGeneratorBuildStep):
                raise AgentGeneratorConfigurationParameterTypeError(
                    agent_generator_filepath=sys.modules[cls.__module__].__file__,
                    parameter_name="agent_generator_build_steps",
                    parameter_type="BaseAgentGeneratorBuildStep",
                )

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({str(self.agent_generator_id)})"

    def __repr__(self) -> str:
        return (
            f"AgentGenerator(agent_type={self.agent_type!r}, name={self.name!r}, "
            f"parameters={self.parameters!r})"
        )

    @abstractmethod
    async def on_agent_generator_started(self) -> None: ...

    @abstractmethod
    async def on_agent_generator_completed(self) -> None: ...

    @abstractmethod
    async def on_agent_generator_stopped(self) -> None: ...

    @abstractmethod
    async def on_agent_generator_cancelled(self) -> None: ...

    @abstractmethod
    async def on_agent_generator_errored(self, exception: Exception) -> None: ...

    async def start_agent_generator(self) -> None:
        if self.status.state == AgentGeneratorState.RUNNING:
            raise AgentGeneratorAlreadyRunningError(
                agent_generator_str=str(self),
                error_message=(
                    "The agent generator cannot be started because it is already "
                    "building an agent."
                ),
            )

        # Clear the signal to the agent generator to stop running if it is set, so it
        # won't instantly stop.
        self.stop_agent_generator_event.clear()

        # The agent generator is now started.
        self.status.transition_to_started()
        try:
            await self.on_agent_generator_started()
        except AgentGeneratorStartError as exc:
            # The agent generator is now initialized.
            self.status.transition_to_initialized()
            raise AgentGeneratorStartFrameworkError(
                agent_generator_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            )
        except Exception as exc:
            self.agent_generator_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The agent generator is now fatally errored.
            self.status.transition_to_fatal(
                agent_generator_str=str(self),
                exception=exc,
            )
            raise exc

        self._agent_generator_task = asyncio.create_task(self._run_agent_generator())

    async def stop_agent_generator(self) -> None:
        if self.status.state != AgentGeneratorState.RUNNING:
            raise AgentGeneratorNotRunningError(
                agent_generator_str=str(self),
                error_message=(
                    "The agent generator cannot be stopped because it is not building "
                    "an agent."
                ),
            )

        try:
            await self.on_agent_generator_stopped()
        except AgentGeneratorStopError as exc:
            # The agent generator has not changed from its building state.
            self.status.transition_to_building()
            raise AgentGeneratorStopFrameworkError(
                agent_generator_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            )
        except Exception as exc:
            self.agent_generator_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The agent generator is now fatally errored.
            self.status.transition_to_fatal(
                agent_generator_str=str(self),
                exception=exc,
            )
            raise exc

        # Signal to the agent generator runtime to stop.
        self.stop_agent_generator_event.set()

    async def cancel_agent_generator(self) -> None:
        if self.status.state != AgentGeneratorState.RUNNING:
            raise AgentGeneratorNotRunningError(
                agent_generator_str=str(self),
                error_message=(
                    "The agent generator cannot be cancelled because it is not "
                    "building an agent."
                ),
            )

        # Cancel the agent generator.
        self._agent_generator_task.cancel()

        # Wait for the task to finish. Then remove the task reference.
        while not self._agent_generator_task.done():
            await asyncio.sleep(0.1)
        self._agent_generator_task = None

        try:
            await self.on_agent_generator_cancelled()
        except Exception as exc:
            self.agent_generator_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The agent generator is now fatally errored.
            self.status.transition_to_fatal(
                agent_generator_str=str(self),
                exception=exc,
            )
            raise exc

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

                # Returning from `on_agent_generator_building()` occurs either when it
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
                framework_exc = AgentGeneratorBuildFrameworkError(
                    agent_generator_str=str(self),
                    error_message=exc.message,
                    detail=exc.detail,
                )
                # The agent generator is now errored.
                self.status.transition_to_errored(exception=framework_exc)
                try:
                    # `on_agent_generator_errored()` should receive the unwrapped 'raw'
                    # exception.
                    await self.on_agent_generator_errored(exception=exc)
                except Exception as exc:
                    self.agent_generator_logger.opt(ansi=True).error(
                        "<bold><red>{}</></>",
                        traceback.format_exc(),
                    )
                    # The agent generator is now fatally errored.
                    self.status.transition_to_fatal(
                        agent_generator_str=str(self),
                        exception=exc,
                    )
        except Exception as exc:
            self.agent_generator_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The agent generator is now fatally errored.
            self.status.transition_to_fatal(
                agent_generator_str=str(self),
                exception=exc,
            )
            try:
                await self.on_agent_generator_errored(exc)
            except Exception as exc:
                self.agent_generator_logger.opt(ansi=True).error(
                    "<bold><red>{}</></>",
                    traceback.format_exc(),
                )
                self.status.transition_to_fatal(
                    agent_generator_str=str(self),
                    exception=exc,
                )
