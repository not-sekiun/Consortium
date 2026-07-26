import pathlib
import sys
import traceback
import types
import uuid
from typing import TYPE_CHECKING, Any, final, get_type_hints

from loguru import logger
from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.components import (
    ComponentLifeCycle,
    ComponentLifeCycleExceptions,
    ComponentLifeCycleFatalContext,
    State,
)
from consortium.framework._core.event_logging.event_log import EventLog
from consortium.framework._core.event_logging.event_logger import EventLogger
from consortium.framework._core.framework_exceptions.agent_generators_framework_exceptions import (
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
    DuplicateAgentGeneratorBuildStepNameError,
    MissingAgentGeneratorBuildStepConfigurationParameterError,
    MissingAgentGeneratorConfigurationParameterError,
)
from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    ComponentNotRunningError,
)
from consortium.framework.signal_exceptions import (
    _component_signal_exceptions as sig_excs,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import construct_services_dataclass, utc_now

if TYPE_CHECKING:
    # This is used for type checking BaseAgentGeneratorBuildStep another runtime import
    # is within BaseAgentGenerator for actually instantiating the service
    from consortium.server.services.agent_templates_payloads_service import (
        AgentTemplatesPayloadsService,
    )


class _BaseAgentGeneratorBuildStepModel(BaseModel):
    name: str
    description: str


class BaseAgentGeneratorBuildStep(ComponentLifeCycle):
    """A single step in an agent generator's build pipeline.

    Subclasses implement build() to perform one discrete stage of the agent creation
    process (compilation, signing, packaging, uploading, etc.). Steps run sequentially
    within a BaseAgentGenerator and share a mutable SimpleNamespace environment so
    earlier steps can pass state (file paths, keys, metadata, etc.) to later ones.

    Attributes:
        name: Unique display name for this build step. Required.
        description: Human-readable explanation of what this step does.
        event_logger: Event logger shared with the owning agent generator, so events
            recorded by every build step appear together in the generator's single
            consolidated event log. Injected by the generator before the step runs;
            None until then.
    """

    name: str
    description: str = ""

    # Only the runtime slot has a build step specific class. The remaining slots keep the
    # generic component errors, so a build step start or stop failure reports as a
    # component exactly as it did before this set existed.
    _component_life_cycle_exceptions = ComponentLifeCycleExceptions(
        runtime=AgentGeneratorBuildStepRuntimeError,
    )

    def __init__(self, agent_templates_payload_service: AgentTemplatesPayloadsService):
        """Initialize the build step with a reference to the agent templates payload service.

        Args:
            agent_templates_payload_service: Service providing storage and retrieval of
                payload artifacts produced or consumed by this build step.
        """
        self.datetime_started = None
        self.datetime_stopped = None
        self.environment = types.SimpleNamespace()
        self.parameters = {}
        self.logger = logger.bind(
            logger_name=f"Agent Generator Build Step {self}",
            logger_type=LoggerType.GENERATOR_LOGGER,
        )
        # Injected by the owning agent generator in run() so every build step reports
        # into the generator's shared event log. Mirrors to this step's own system
        # logger.
        self.event_logger: EventLogger | None = None
        self.agent_templates_payload_service = agent_templates_payload_service

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

        cls.root_directory = pathlib.Path(sys.modules[cls.__module__].__file__).parent
        cls.services = construct_services_dataclass(server_singletons=server_singletons)

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
        return f"'{self.name}'"

    def __repr__(self) -> str:
        return (
            f"AgentGeneratorBuildStep("
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f")"
        )

    @property
    def time_elapsed_in_seconds(self) -> float | None:
        """Wall-clock duration of the most recent run in seconds.

        Returns:
            Elapsed seconds between start and stop, or None if the step has not
            completed or was never started.
        """
        if self.datetime_started and self.datetime_stopped:
            return (self.datetime_stopped - self.datetime_started).total_seconds()
        return None

    async def build(self, parameters: dict) -> None:
        """Execute the build logic for this step.

        Override to implement the step's discrete unit of work. The shared environment
        namespace is accessible via self.environment, and agent_templates_payload_service
        is available for storing build artifacts.

        Args:
            parameters: The generator's configuration parameters passed through from
                the owning BaseAgentGenerator instance.
        """
        ...

    @final
    async def on_started(self) -> None:
        self.datetime_started = utc_now()

    @final
    async def on_running(self) -> None:
        await self.build(parameters=self.parameters)

    @final
    async def on_completed(self) -> None:
        self.datetime_stopped = utc_now()

    @final
    async def on_stopped(self) -> None:
        self.datetime_stopped = utc_now()

    @final
    async def on_cancelled(self) -> None:
        self.datetime_stopped = utc_now()

    @final
    async def on_errored(self, error: AgentGeneratorBuildStepRuntimeError) -> None:
        self.datetime_stopped = utc_now()
        # Record into the shared event log when available (it is injected by the
        # generator before the step runs), otherwise fall back to the system logger.
        if self.event_logger is not None:
            self.event_logger.failure(str(error))
        else:
            self.logger.error(error)

    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
        """Hook invoked when an unrecoverable error occurs in the build step lifecycle.

        Args:
            exc: The underlying exception that triggered the fatal transition.
            fatal_context: The lifecycle phase (starting, running, stopping, etc.)
                during which the fatal error occurred.
        """
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
        event_logger: EventLogger,
    ) -> None:
        """Start this build step with the provided parameters and environment, blocking until done.

        This is the entry point called by BaseAgentGenerator during pipeline execution.
        It injects the shared environment, parameter set, and event logger before
        starting the component lifecycle.

        Args:
            parameters: Key-value configuration parameters forwarded from the generator.
            environment: Shared namespace that allows steps to read and write state
                across the pipeline.
            event_logger: Event logger sharing the generator's event log, so events
                recorded by this step appear alongside those of every other step.
        """
        # Override `environment` and `event_logger` set during initialization to the
        # ones provided by the AgentGenerator.
        self.environment = environment
        self.parameters = parameters
        self.event_logger = event_logger
        await super().start()
        await self.wait_until_stopped()

    def reset(self) -> None:
        """Reset timing state and status so the step can be reused in a subsequent generator run."""
        self.datetime_started = None
        self.datetime_stopped = None
        self.parameters = {}
        self.event_logger = None
        super().reset()

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the build step's current state to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the step name, description, start and stop
            timestamps, elapsed time in seconds, and current lifecycle status.
        """
        return {
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
        """Serialize a compact reference to this build step.

        Returns:
            A dictionary containing only the step name, suitable for embedding as a
            lightweight reference in other JSON objects.
        """
        return {
            "name": self.name,
        }


class _BaseAgentGeneratorParametersModel(BaseModel):
    name: str
    description: str
    parameters: dict[str, JsonValue]


class _BaseAgentGeneratorModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_generator_build_steps: list[type[BaseAgentGeneratorBuildStep]]


class BaseAgentGenerator(ComponentLifeCycle):
    """Orchestrates a pipeline of build steps to produce a deployable agent payload.

    Subclasses declare a list of BaseAgentGeneratorBuildStep classes that are
    instantiated and executed sequentially at run time. A shared SimpleNamespace
    environment allows earlier steps to pass state (file paths, signing keys,
    compiled artifacts, etc.) to later ones.

    Attributes:
        agent_generator_build_steps: Ordered sequence of build step classes. Declared
            at the class level and converted to instances in __init__.
        event_logger: Generator-wide event logger. Every build step is given a child
            logger that shares this logger's underlying event log, so all build steps
            report into one consolidated, client-facing event log. Entries are
            optionally mirrored to the relevant system logger.
    """

    agent_generator_build_steps: list[type[BaseAgentGeneratorBuildStep]] = None

    # Raise agent generator errors directly from the shared lifecycle instead of raising
    # generic component errors and remapping them here, which would format the message
    # twice.
    _component_life_cycle_exceptions = ComponentLifeCycleExceptions(
        start=AgentGeneratorStartError,
        stop=AgentGeneratorStopError,
        runtime=AgentGeneratorRuntimeError,
        not_running=AgentGeneratorNotRunningError,
        already_running=AgentGeneratorAlreadyRunningError,
    )

    def __init__(
        self,
        name: str = "",
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Create a new agent generator instance with the given name, description, and parameters.

        Args:
            name: Human-readable label for this generator run, used in log messages
                and serialized output.
            description: Optional longer description of what this particular run produces.
            parameters: Key-value configuration values passed to each build step. Must
                satisfy the options declared by the owning agent template.
        """
        # See starred Claude code conversation "circular import in agent framework"
        # for framework registry module fix
        from consortium.server.services.agent_templates_payloads_service import (
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
        self.datetime_created = utc_now()
        self.environment = types.SimpleNamespace()

        self.logger = logger.bind(
            logger_name=f"Agent Generator {self}",
            logger_type=LoggerType.GENERATOR_LOGGER,
        )
        self.event_logger = EventLogger(
            event_log=EventLog(subject_id=self.agent_generator_id),
            system_logger=self.logger,
        )

        self._current_agent_generator_build_step = None
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        if "on_running" in cls.__dict__:
            raise AgentGeneratorOverridesFinalMethodError(
                agent_generator_filepath=sys.modules[cls.__module__].__file__,
                method_name="on_running",
            )

        cls.root_directory = pathlib.Path(sys.modules[cls.__module__].__file__).parent
        cls.services = construct_services_dataclass(server_singletons=server_singletons)

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

        # Enforce that build step names are unique within the agent generator so they
        # can serve as stable identifiers for each step.
        seen = set()
        for agent_generator_build_step in cls.agent_generator_build_steps:
            if agent_generator_build_step.name not in seen:
                seen.add(agent_generator_build_step.name)
            else:
                raise DuplicateAgentGeneratorBuildStepNameError(
                    agent_generator_filepath=sys.modules[cls.__module__].__file__,
                    agent_generator_build_step_name=agent_generator_build_step.name,
                )

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

    async def on_started(self) -> None:
        """Hook invoked before build steps begin executing.

        Override to perform any initialization that must complete before the build
        pipeline starts, such as preparing directories or acquiring external resources.
        """
        ...

    async def on_completed(self) -> None:
        """Hook invoked after all build steps finish successfully.

        Override to perform cleanup, notifications, or post-processing after a
        successful build.
        """
        ...

    @final
    async def on_running(self) -> None:
        # Reset each build step before running them in case the agent generator is
        # started more than once.
        for agent_generator_build_step in self.agent_generator_build_steps:
            agent_generator_build_step.reset()

        total_build_steps = len(self.agent_generator_build_steps)
        for build_step_number, agent_generator_build_step in enumerate(
            self.agent_generator_build_steps, start=1
        ):
            self._current_agent_generator_build_step = agent_generator_build_step

            # Report the pipeline's orchestration progress into the shared event log
            # and hand each step a child logger over that same log so any events the
            # step records itself land alongside these orchestration events.
            self.event_logger.update_progress(
                percent_complete=((build_step_number - 1) / total_build_steps) * 100,
                message=f"Running build step '{agent_generator_build_step.name}'",
            )
            self.event_logger.info(
                f"Running build step '{agent_generator_build_step.name}' "
                f"({build_step_number}/{total_build_steps})"
            )
            await agent_generator_build_step.run(
                parameters=self.parameters,
                environment=self.environment,
                event_logger=self.event_logger.create_child_logger(
                    system_logger=agent_generator_build_step.logger,
                ),
            )

            # Since we are in the agent generator's on_running() method to communicate
            # upwards that the agent generator failed we must throw a
            # ComponentRuntimeError signalling error from consortium.framework.exceptions
            # module. We can throw the generic ComponentRuntimeError because it will be
            # caught and translated by the _construct_component_runtime_error_* methods
            # in this class to the appropriate AgentGeneratorRuntimeError.
            # TODO: Allow a build step to error but not cut the pipeline out early with
            #  an exit_on_fail boolean on agent generator build steps, default to true
            #  and have it be opt in false
            if agent_generator_build_step.status.state in (State.ERRORED, State.FATAL):
                raise sig_excs.ComponentRuntimeError(
                    message=f"The following agent generator build step(s) failed: {agent_generator_build_step}",
                    detail={
                        "errored_agent_generator_build_steps": [
                            agent_generator_build_step.name
                        ],
                    },
                )

            if self.stop_event.is_set():
                break
        else:
            # Every build step ran without the pipeline being stopped early.
            self.event_logger.update_progress(
                percent_complete=100.0,
                message="All build steps completed",
            )
            self.event_logger.success("All build steps completed successfully")

    async def on_stopped(self) -> None:
        """Hook invoked when the generator is stopped before all steps complete.

        Override to clean up resources that were allocated before the generator was halted.
        """
        ...

    async def on_cancelled(self) -> None:
        """Hook invoked when the generator run is cancelled externally.

        Override to clean up resources when the build is aborted mid-pipeline.
        """
        ...

    async def on_errored(self, error: AgentGeneratorRuntimeError) -> None:
        """Hook invoked when a runtime error occurs during execution.

        Args:
            error: The structured runtime error describing what failed and why.
        """
        # Recording through the event logger both surfaces the failure in the
        # client-facing event log and mirrors it to the generator's system logger.
        self.event_logger.failure(str(error))

    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
        """Hook invoked when an unrecoverable error occurs in the generator lifecycle.

        Args:
            exc: The underlying exception that triggered the fatal transition.
            fatal_context: The lifecycle phase (starting, running, stopping, etc.)
                during which the fatal error occurred.
        """
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

    # start() and cancel() below add no behaviour and exist purely to carry their
    # documentation. The documentation generator infers docstrings statically and does not
    # follow the MRO, so the agent generator specific `Raises:` entries have to be
    # physically present on this class to be published. stop() does carry behaviour, in
    # the build step teardown below.
    #
    # Do NOT reintroduce a try/except in any of them to convert component errors into
    # agent generator errors. The lifecycle already raises the agent generator errors
    # directly via `_component_life_cycle_exceptions`; catching and re-raising would pass
    # an already formatted message back through a second template and nest the prefix.

    async def start(self) -> None:
        """Start the agent generator and begin executing its build pipeline.

        Raises:
            AgentGeneratorAlreadyRunningError: If the generator is already in a running state.
            AgentGeneratorStartError: If the generator fails to start due to a lifecycle error.
        """
        await super().start()

    async def cancel(self) -> None:
        """Cancel the agent generator run.

        Raises:
            AgentGeneratorNotRunningError: If the generator is not currently running.
        """
        await super().cancel()

    async def stop(self) -> None:
        """Stop the generator and interrupt the currently executing build step.

        Also attempts to stop the active build step if one is running.

        Raises:
            AgentGeneratorNotRunningError: If the generator is not currently running.
            AgentGeneratorStopError: If the generator fails to stop cleanly.
        """
        await super().stop()

        if self._current_agent_generator_build_step is not None:
            try:
                await self._current_agent_generator_build_step.stop()
            # If the build step is not running, we can ignore it since we are stopping
            # the agent generator. Also since on_stopped() is supposed to be
            # non-overridable we should not have a *StopError raised from there.
            except ComponentNotRunningError:
                pass

    def to_json(
        self,
        limit: int = 10,
        offset: int | None = None,
        include_event_log_entries: bool = True,
    ) -> dict[str, JsonValue]:
        """Serialize the generator's current state to a JSON-compatible dictionary.

        Args:
            limit: Maximum number of event log entries to include.
            offset: Sequence offset to start the event log window from. If None, the
                tail (most recent entries up to limit) is returned.
            include_event_log_entries: When False, the event log's entries list is
                omitted (its total count and current progress are still included). Used
                by collection endpoints to keep list responses bounded.

        Returns:
            A dictionary containing the generator ID, name, description, parameters,
            status, creation timestamp, event log, build step states, agent type,
            compatible listener types, and a reference to the creating agent template.
        """
        return {
            "agent_generator_id": str(self.agent_generator_id),
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status.to_json(),
            "event_log": self.event_logger.to_json(
                limit=limit, offset=offset, include_entries=include_event_log_entries
            ),
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
            "creating_agent_template": self.creating_agent_template.to_json_reference(),
        }

    def to_json_reference(self) -> dict[str, str]:
        """Serialize a compact reference to this generator.

        Returns:
            A dictionary containing only the generator ID and name, suitable for
            embedding as a lightweight foreign key reference in other JSON objects.
        """
        return {
            "agent_generator_id": str(self.agent_generator_id),
            "name": self.name,
        }
