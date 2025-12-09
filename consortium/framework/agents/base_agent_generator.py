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
from typing import Any, final, get_type_hints

from loguru import logger
from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

from consortium.framework._components import (
    ComponentLifeCycle,
    ComponentLifeCycleFatalContext,
)
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.exceptions.agent_generators_framework_exceptions import (
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
    MissingAgentGeneratorConfigurationParameterError,
    RequiredAgentGeneratorBuildStepConfigurationParameterNotDeclaredError,
)
from consortium.server.objects.agent_generator_objects import (
    AgentGeneratorBuildStepStatus,
    AgentGeneratorState,
    AgentGeneratorStatus,
)
from consortium.server.server_logging import LoggerType


class _BaseAgentGeneratorBuildStepParametersModel(BaseModel):
    name: str
    description: str
    ignore_failure: bool


class BaseAgentGeneratorBuildStep(ABC):
    name: str
    description: str = ""
    ignore_failure: bool = False

    def __init__(self):
        self.agent_generator_build_step_id = uuid.uuid4()
        self.datetime_started = None
        self.datetime_stopped = None
        self.status = AgentGeneratorBuildStepStatus()
        self.logger = logger.bind(
            logger_name=f"Agent Generator Build Step {self}",
            logger_type=LoggerType.GENERATOR_LOGGER,
        )

        self.working_directory = Path(inspect.getsourcefile(self.__class__)).parent

    def __init_subclass__(cls, **kwargs):
        expected_attrs_and_types_map = get_type_hints(cls)

        # Check all attributes exist
        for attr in expected_attrs_and_types_map.keys():
            if not hasattr(cls, attr):
                raise MissingAgentGeneratorConfigurationParameterError(
                    agent_generator_filepath=sys.modules[cls.__module__].__file__,
                    parameter_name=attr,
                )

        # Check all class attributes are of the expected type
        try:
            _BaseAgentGeneratorBuildStepParametersModel(
                name=cls.name,
                description=cls.description,
                ignore_failure=cls.ignore_failure,
            )
        except ValidationError as exc:
            attr = exc.errors()[0]["loc"][0]
            raise AgentGeneratorBuildStepConfigurationParameterTypeError(
                agent_generator_build_step_str=cls.name,
                parameter_name=attr,
                parameter_type=str(expected_attrs_and_types_map[attr]),
            )

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.agent_generator_build_step_id)})"

    def __repr__(self) -> str:
        return (
            f"AgentGeneratorBuildStep("
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"ignore_failure={self.ignore_failure}"
            f")"
        )

    @abstractmethod
    async def on_running(
        self,
        stop_event: asyncio.Event,
        parameters: dict,
        environment: SimpleNamespace,
    ): ...

    async def start(
        self,
        stop_event: asyncio.Event,
        parameters: dict,
        environment: SimpleNamespace,
    ):
        self.datetime_started = datetime.now()
        self.status.transition_to_running()
        try:
            await self.on_running(
                stop_event=stop_event,
                parameters=parameters,
                environment=environment,
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


class _BaseAgentGeneratorParametersModel(BaseModel):
    name: str
    description: str
    parameters: dict[str, JsonValue]


class _BaseAgentGeneratorModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_generator_build_steps: list[BaseAgentGeneratorBuildStep]


class BaseAgentGenerator(ComponentLifeCycle):
    agent_generator_build_steps: list[BaseAgentGeneratorBuildStep] = None

    def __init__(
        self,
        name: str = "",
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        if parameters is None:
            parameters = {}

        try:
            _BaseAgentGeneratorParametersModel(
                name=name,
                description=description,
                parameters=parameters,
            )
        except ValidationError as exc:
            for err in exc.errors():
                raise AgentGeneratorCreationParameterTypeError(
                    agent_generator_str=sys.modules[self.__module__].__file__,
                    parameter_name=err["loc"][0],
                    parameter_type=get_type_hints(_BaseAgentGeneratorParametersModel)[
                        err["loc"]
                    ],
                ) from None

        self.name = name
        self.description = description
        self.parameters = parameters

        self.agent_generator_id = uuid.uuid4()
        self.datetime_created = datetime.now()
        self.environment = SimpleNamespace()
        self.logger = logger.bind(
            logger_name=f"Agent Generator {self}",
            logger_type=LoggerType.GENERATOR_LOGGER,
        )
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "agent_generator_build_steps"):
            raise MissingAgentGeneratorConfigurationParameterError(
                agent_generator_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="agent_generator_build_steps",
            )
        if cls.agent_generator_build_steps is None:
            cls.agent_generator_build_steps = []

        try:
            _BaseAgentGeneratorModel(
                agent_generator_build_steps=cls.agent_generator_build_steps,
            )
        except ValidationError as exc:
            for err in exc.errors():
                raise AgentGeneratorConfigurationParameterTypeError(
                    agent_generator_filepath=sys.modules[cls.__module__].__file__,
                    parameter_name=err["loc"][0],
                    parameter_type="list[BaseAgentGeneratorBuildStep]",
                ) from None

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.agent_generator_id)})"

    def __repr__(self) -> str:
        return (
            f"AgentGenerator("
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"parameters={self.parameters!r}"
            f")"
        )

    async def on_started(self) -> None: ...

    async def on_completed(self) -> None: ...

    # TODO: Maybe think of a stricter way to prevent overriding this method.
    @final
    async def on_running(self) -> None:
        for agent_generator_build_step in self.agent_generator_build_steps:
            await agent_generator_build_step.start(
                stop_event=self.stop_event,
                parameters=self.parameters,
                environment=self.environment,
            )
            if self.stop_event.is_set():
                break

    async def on_stopped(self) -> None: ...

    async def on_cancelled(self) -> None: ...

    async def on_errored(self, error: AgentGeneratorBuildError) -> None:
        self.logger.error(error)

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

    def to_json(self):
        return {
            "agent_generator_id": str(self.agent_generator_id),
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status.to_json(),
            "datetime_created": self.datetime_created.isoformat(),
            "agent_generator_build_steps": [
                agent_generator_build_step.to_json()
                for agent_generator_build_step in self.agent_generator_build_steps
            ],
            "agent_type": self.agent_type.to_json(),
            # `creating_agent_template` is assigned to the agent generator class by the
            # agent profile loader at load time.
            "creating_agent_template": {
                "agent_template_id": str(
                    self.creating_agent_template.agent_template_id,
                ),
                "name": self.creating_agent_template.name,
            },
        }
