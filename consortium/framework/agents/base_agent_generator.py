import inspect
import pathlib
import sys
import traceback
import types
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, final, get_type_hints

from loguru import logger
from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework._components import (
    ComponentLifeCycle,
    ComponentLifeCycleFatalContext,
    State,
)
from consortium.framework.exceptions import (
    _component_framework_exceptions as framework_excs,
)
from consortium.server.exceptions.consortium_exceptions.agent_generators_consortium_exceptions import (
    AgentGeneratorAlreadyRunningError,
    AgentGeneratorBuildStepConfigurationParameterTypeError,
    AgentGeneratorBuildStepOverridesFinalMethodError,
    AgentGeneratorBuildStepRuntimeError,
    AgentGeneratorConfigurationParameterTypeError,
    AgentGeneratorCreationParameterTypeError,
    AgentGeneratorNotRunningError,
    AgentGeneratorOverridesFinalMethodError,
    AgentGeneratorRuntimeError,
    AgentGeneratorStartError,
    AgentGeneratorStopError,
    MissingAgentGeneratorBuildStepConfigurationParameterError,
    MissingAgentGeneratorConfigurationParameterError,
)
from consortium.server.exceptions.consortium_exceptions.components_consortium_exceptions import (
    ComponentAlreadyRunningError,
    ComponentNotRunningError,
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import construct_services_namespace_object

if TYPE_CHECKING:
    # This is used for type checking BaseAgentGeneratorBuildStep another runtime import
    # is within BaseAgentGenerator for actually instantiating the service
    from consortium.server.services.agent_templates_payload_service import (
        AgentTemplatesPayloadsService,
    )


class _BaseAgentGeneratorBuildStepModel(BaseModel):
    name: str
    description: str


class BaseAgentGeneratorBuildStep(ComponentLifeCycle):
    name: str
    description: str = ""

    def __init__(self, agent_templates_payload_service: AgentTemplatesPayloadsService):
        self.agent_generator_build_step_id = uuid.uuid4()
        self.datetime_started = None
        self.datetime_stopped = None
        self.environment = types.SimpleNamespace()
        self.parameters = {}
        self.logger = logger.bind(
            logger_name=f"Agent Generator Build Step {self}",
            logger_type=LoggerType.GENERATOR_LOGGER,
        )
        self.agent_templates_payload_service = agent_templates_payload_service
        self.working_directory = pathlib.Path(
            inspect.getsourcefile(self.__class__)
        ).parent

        super().__init__()

    def __init_subclass__(cls, **kwargs):
        for method_name in (
            "on_started",
            "on_running",
            "on_completed",
            "on_stopped",
            "on_cancelled",
            "on_errored",
        ):
            if method_name in cls.__dict__:
                raise AgentGeneratorBuildStepOverridesFinalMethodError(
                    agent_generator_build_step_filepath=sys.modules[
                        cls.__module__
                    ].__file__,
                    method_name=method_name,
                )

        cls.services = construct_services_namespace_object(
            server_singletons=server_singletons
        )

        expected_attrs_and_types_map = get_type_hints(cls)

        # Check all attributes exist
        for attr in expected_attrs_and_types_map.keys():
            if not hasattr(cls, attr):
                raise MissingAgentGeneratorBuildStepConfigurationParameterError(
                    agent_generator_build_step_filepath=sys.modules[
                        cls.__module__
                    ].__file__,
                    parameter_name=attr,
                )

        # Check all class attributes are of the expected type
        try:
            _BaseAgentGeneratorBuildStepModel(
                name=cls.name,
                description=cls.description,
            )
        except ValidationError as exc:
            attr = exc.errors()[0]["loc"][0]
            raise AgentGeneratorBuildStepConfigurationParameterTypeError(
                agent_generator_build_step_str=cls.name,
                parameter_name=attr,
                parameter_type=str(expected_attrs_and_types_map[attr]),
            ) from None

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.agent_generator_build_step_id)})"

    def __repr__(self) -> str:
        return (
            f"AgentGeneratorBuildStep("
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f")"
        )

    @property
    def time_elapsed_in_seconds(self) -> float | None:
        if self.datetime_started and self.datetime_stopped:
            return (self.datetime_stopped - self.datetime_started).total_seconds()
        return None

    async def build(self, parameters: dict) -> None: ...

    @final
    async def on_started(self) -> None:
        self.datetime_started = datetime.now()

    @final
    async def on_running(self) -> None:
        await self.build(parameters=self.parameters)

    @final
    async def on_completed(self) -> None:
        self.datetime_stopped = datetime.now()

    @final
    async def on_stopped(self) -> None:
        self.datetime_stopped = datetime.now()

    @final
    async def on_cancelled(self) -> None:
        self.datetime_stopped = datetime.now()

    @final
    async def on_errored(self, error: AgentGeneratorBuildStepRuntimeError) -> None:
        self.datetime_stopped = datetime.now()
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
        self.logger.opt(colors=True).error(
            "<bold><red>Fatal error occurred within agent generator build step {} while it was {}:</></>\n{}",
            str(self),
            ctx_to_str_map[fatal_context],
            traceback.format_exc(),
        )

    async def run(
        self,
        parameters: dict,
        environment: types.SimpleNamespace,
    ) -> None:
        # Override `environment` set during initialization to the ones provided by the
        # AgentGenerator.
        self.environment = environment
        self.parameters = parameters
        await super().start()
        await self.wait_until_stopped()

    def reset(self) -> None:
        self.datetime_started = None
        self.datetime_stopped = None
        self.parameters = {}
        super().reset()

    def to_json(self) -> dict[str, Any]:
        return {
            "agent_generator_build_step_id": str(self.agent_generator_build_step_id),
            "name": self.name,
            "description": self.description,
            "datetime_started": self.datetime_started.isoformat()
            if self.datetime_started
            else None,
            "datetime_stopped": self.datetime_stopped.isoformat()
            if self.datetime_stopped
            else None,
            "time_elapsed_in_seconds": self.time_elapsed_in_seconds,
            "status": self.status.to_json(),
        }

    def to_json_reference(self) -> dict[str, str]:
        return {
            "agent_generator_build_step_id": str(self.agent_generator_build_step_id),
            "name": self.name,
        }

    def _construct_component_runtime_error_from_framework_runtime_error(
        self,
        error: ComponentRuntimeError,
    ) -> AgentGeneratorBuildStepRuntimeError:
        return AgentGeneratorBuildStepRuntimeError(
            agent_generator_build_step_str=str(self),
            error_message=error.message,
            detail=error.detail,
        )

    def _construct_component_runtime_error_from_unhandled_exception(
        self,
        exc: Exception,
    ) -> AgentGeneratorBuildStepRuntimeError:
        return AgentGeneratorBuildStepRuntimeError(
            agent_generator_build_step_str=str(self),
            error_message=(
                f"An unhandled exception was raised while running. "
                f"{type(exc).__name__}: {exc}"
            ),
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )


class _BaseAgentGeneratorParametersModel(BaseModel):
    name: str
    description: str
    parameters: dict[str, JsonValue]


class _BaseAgentGeneratorModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_generator_build_steps: list[type[BaseAgentGeneratorBuildStep]]


class BaseAgentGenerator(ComponentLifeCycle):
    agent_generator_build_steps: list[type[BaseAgentGeneratorBuildStep]] = None

    def __init__(
        self,
        name: str = "",
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        # See starred Claude code conversation "circular import in agent framework"
        # for framework registry module fix
        from consortium.server.services.agent_templates_payload_service import (
            AgentTemplatesPayloadsService,
        )

        if parameters is None:
            parameters = {}
        # Manually validate name first so we can reference the name in subsequent
        # validation errors
        if not isinstance(name, str):
            raise AgentGeneratorCreationParameterTypeError(
                agent_generator_str=self.__class__.__name__,
                parameter_name="name",
                parameter_type=str(str),
            ) from None

        try:
            _BaseAgentGeneratorParametersModel(
                name=name,
                description=description,
                parameters=parameters,
            )
        except ValidationError as exc:
            for err in exc.errors():
                raise AgentGeneratorCreationParameterTypeError(
                    agent_generator_str=name,
                    parameter_name=err["loc"][0],
                    parameter_type=str(
                        get_type_hints(_BaseAgentGeneratorParametersModel)[err["loc"]]
                    ),
                ) from None

        self.name = name
        self.description = description
        self.parameters = parameters

        self.agent_generator_id = uuid.uuid4()
        # self.creating_agent_template is assigned as a class variable at load time
        self.agent_templates_payload_service = AgentTemplatesPayloadsService(
            agent_template_id=self.creating_agent_template.agent_template_id,
        )
        self.agent_generator_build_steps: list[BaseAgentGeneratorBuildStep] = [
            agent_generator_build_step(
                agent_templates_payload_service=self.agent_templates_payload_service
            )
            for agent_generator_build_step in self.__class__.agent_generator_build_steps
        ]
        self.datetime_created = datetime.now()
        self.environment = types.SimpleNamespace()

        self.logger = logger.bind(
            logger_name=f"Agent Generator {self}",
            logger_type=LoggerType.GENERATOR_LOGGER,
        )

        self._current_agent_generator_build_step = None
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        if "on_running" in cls.__dict__:
            raise AgentGeneratorOverridesFinalMethodError(
                agent_generator_filepath=sys.modules[cls.__module__].__file__,
                method_name="on_running",
            )

        cls.services = construct_services_namespace_object(
            server_singletons=server_singletons
        )

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
            raise AgentGeneratorConfigurationParameterTypeError(
                agent_generator_filepath=sys.modules[cls.__module__].__file__,
                parameter_name=str(exc.errors()[0]["loc"][0]),
                parameter_type=get_type_hints(_BaseAgentGeneratorModel)[
                    exc.errors()[0]["loc"][0]
                ],
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

    @final
    async def on_running(self) -> None:
        # Reset each build step before running them in case the agent generator is
        # started more than once.
        for agent_generator_build_step in self.agent_generator_build_steps:
            agent_generator_build_step.reset()

        for agent_generator_build_step in self.agent_generator_build_steps:
            self._current_agent_generator_build_step = agent_generator_build_step
            await agent_generator_build_step.run(
                parameters=self.parameters,
                environment=self.environment,
            )

            # Since we are in the agent generator's on_running() method to communicate
            # upwards that the agent generator failed we must throw a
            # ComponentRuntimeError signalling error from consortium.framework.exceptions
            # module. We can throw the generic ComponentRuntimeError because it will be
            # caught and translated by the _construct_component_runtime_error_* methods
            # in this class to the appropriate AgentGeneratorRuntimeError.
            if agent_generator_build_step.status.state in (State.ERRORED, State.FATAL):
                raise framework_excs.ComponentRuntimeError(
                    message=(
                        f"Agent generator build step "
                        f"{agent_generator_build_step} "
                        f"failed while running."
                    ),
                    detail={
                        "agent_generator_build_step_status": (
                            agent_generator_build_step.status.to_json()
                        ),
                    },
                )

            if self.stop_event.is_set():
                break

    async def on_stopped(self) -> None: ...

    async def on_cancelled(self) -> None: ...

    async def on_errored(self, error: AgentGeneratorRuntimeError) -> None:
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
        self.logger.opt(colors=True).error(
            "<bold><red>Fatal error occurred within agent generator {} while it was {}:</></>\n{}",
            str(self),
            ctx_to_str_map[fatal_context],
            traceback.format_exc(),
        )

    async def start(self) -> None:
        try:
            await super().start()
        except ComponentAlreadyRunningError:
            raise AgentGeneratorAlreadyRunningError(
                agent_generator_str=str(self),
            ) from None
        except ComponentStartError as exc:
            raise AgentGeneratorStartError(
                agent_generator_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None

    async def stop(self) -> None:
        try:
            await super().stop()
        except ComponentNotRunningError:
            raise AgentGeneratorNotRunningError(
                agent_generator_str=str(self),
            ) from None
        except ComponentStopError as exc:
            raise AgentGeneratorStopError(
                agent_generator_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None

        if self._current_agent_generator_build_step is not None:
            try:
                await self._current_agent_generator_build_step.stop()
            # If the build step is not running, we can ignore it since we are stopping
            # the agent generator. Also since on_stopped() is supposed to be
            # non-overridable we should not have a *StopError raised from there.
            except ComponentNotRunningError:
                pass

    async def cancel(self) -> None:
        try:
            await super().cancel()
        except ComponentNotRunningError:
            raise AgentGeneratorNotRunningError(
                agent_generator_str=str(self),
            ) from None

    def to_json(self) -> dict[str, Any]:
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
            # Compatible listener types is assigned to the agent generator class by the
            # agent profile loader at load time and referenced from the agent template.
            "compatible_listener_types": list(self.compatible_listener_types),
            # `creating_agent_template` is assigned to the agent generator class by the
            # agent profile loader at load time.
            "creating_agent_template": {
                "agent_template_id": str(
                    self.creating_agent_template.agent_template_id,
                ),
                "label": self.creating_agent_template.label,
                "name": self.creating_agent_template.name,
            },
        }

    def to_json_reference(self) -> dict[str, str]:
        return {
            "agent_generator_id": str(self.agent_generator_id),
            "name": self.name,
        }

    def _construct_component_runtime_error_from_framework_runtime_error(
        self,
        error: ComponentRuntimeError,
    ) -> AgentGeneratorRuntimeError:
        return AgentGeneratorRuntimeError(
            agent_generator_str=str(self),
            error_message=error.message,
            detail=error.detail,
        )

    def _construct_component_runtime_error_from_unhandled_exception(
        self,
        exc: Exception,
    ) -> AgentGeneratorRuntimeError:
        return AgentGeneratorRuntimeError(
            agent_generator_str=str(self),
            error_message=(
                f"An unhandled exception was raised while running. "
                f"{type(exc).__name__}: {exc}"
            ),
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )
