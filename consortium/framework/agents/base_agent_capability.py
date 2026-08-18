import asyncio
from collections.abc import Callable
from enum import StrEnum
from inspect import signature
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, get_type_hints

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCapabilityFatalError,
    DuplicateAgentCapabilityChannelNameError,
    DuplicateAgentCapabilityOptionNameError,
    EmptyAgentCapabilityNameError,
    InvalidAgentCapabilityConfigurationParameterTypeError,
    MissingAgentCapabilityConfigurationParameterError,
)
from consortium.framework._core.utils import (
    format_docstring_to_single_line,
    resolve_component_filepath,
    resolve_validation_error_parameter,
)
from consortium.framework.agents._agent_communicator import _AgentCommunicator
from consortium.framework.agents._channel_buffer import ChannelBuffer
from consortium.framework.agents._resource_limits import CHANNEL_BUFFER_MEMORY_LIMIT
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.channels import Channel
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)
from consortium.framework.signal_exceptions.base_signal_exception import (
    BaseSignalException,
)
from consortium.server.objects.mitre_attack_objects import (
    # MitreAttackTechniqueID,
    resolve_mitre_attack_technique_id,
)
from consortium.server.services.agent_file_manager_service import (
    AgentFileManagerService,
)
from consortium.server.utils import construct_services_dataclass

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent
    from consortium.server.objects.task_objects import Task


class SupportedOS(StrEnum):
    """Operating system identifiers for declaring capability platform compatibility.

    Use these values in BaseAgentCapability.supported_oses to restrict which platforms
    a capability can run on. ANY indicates universal compatibility with no restrictions.
    The DESKTOP and MOBILE class attributes provide pre-built sets of related OS values
    for convenience.
    """

    WINDOWS = "WINDOWS"
    LINUX = "LINUX"
    MACOS = "MACOS"
    ANDROID = "ANDROID"
    IOS = "IOS"
    ANY = "ANY"

    # Add type hinting here for IDE autocompletion support.
    DESKTOP: set[SupportedOS]
    MOBILE: set[SupportedOS]


# Add convenience groupings of supported OSes as class attributes after enum creation.
SupportedOS.DESKTOP = {SupportedOS.WINDOWS, SupportedOS.LINUX, SupportedOS.MACOS}
SupportedOS.MOBILE = {SupportedOS.ANDROID, SupportedOS.IOS}


class AgentLifecycle(StrEnum):
    """Lifecycle stages at which a capability can be configured to trigger.

    Used to indicate when during an agent's registration and check-in lifecycle
    a particular action should be performed.
    """

    ON_REGISTERED = "ON_REGISTERED"
    ON_CHECKED_IN = "ON_CHECKED_IN"


# The stages of `execute()` at which an unexpected exception can escape a capability. The
# value is embedded verbatim in an `AgentCapabilityFatalError` message ("... during the
# {phase} phase.") and its `detail`, so `execute()` can tell the task handler which stage
# failed.
class AgentCapabilityPhase(StrEnum):
    LAUNCH = "launch"
    DISPATCH = "dispatch"
    EXECUTION = "execution"


class _BaseAgentCapabilityModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    authors: set[str]
    requires_admin: bool
    supported_oses: set[SupportedOS | str]
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ]
    mitre_attack_techniques: set[str]
    validating_function: Callable[[dict[str, JsonValue]], None] | None
    channels: set[Channel]


class BaseAgentCapability(_AgentCommunicator):
    """Base class for all agent capabilities that define executable commands.

    Subclasses declare capability metadata as class attributes (name, description,
    options, etc.) and override on_launch and on_execute to control how the command
    is transmitted to the agent and how the response is processed. The framework
    validates all class attributes at subclass definition time via __init_subclass__.

    Attributes:
        name: Unique command identifier used to route incoming task messages.
            Required and must be non-empty.
        description: Human-readable explanation of what this capability does.
        authors: Identifiers for the capability's authors.
        requires_admin: Whether elevated privileges are required on the target
            system to execute this capability.
        supported_oses: Platforms this capability supports. Defaults to
            {SupportedOS.ANY} if not declared.
        options: Configuration options accepted by this capability. Declared as a set
            at the class level; converted to a name-keyed dict at definition time.
        mitre_attack_techniques: MITRE ATT&CK technique IDs associated with this
            capability. Resolved to MitreAttackTechnique objects at definition time.
        validating_function: Optional single-argument callable that validates the full
            resolved option set before execution.
        channels: Byte channels this capability offers an attached client. Declared as a
            set at the class level; converted to a name-keyed dict at definition time.
            On an instance the same name resolves to the running buffers rather than the
            declarations, see __init__.
        task_launch_message: The message sent to the agent on the most recent execute()
            call; set by execute() after on_launch completes.
    """

    name: str
    description: str = ""
    authors: set[str] = None
    requires_admin: bool = False
    supported_oses: set[SupportedOS] = None
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ] = None
    mitre_attack_techniques: set[str] | None = None
    validating_function: Callable[[dict[str, JsonValue]], None] | None = None
    channels: set[Channel] = None
    task_launch_message: TaskLaunchMessageModel | None = None

    def __init__(self, agent: Agent, task: Task):
        """Initialize the capability with the agent and task context for this execution.

        A buffer is created for every declared channel, so `self.channels` maps a channel
        name to the live buffer behind it rather than to the declaration the class
        attribute of the same name holds. The buffers exist from construction, before the
        capability has produced a byte, so a client can attach to a channel that is still
        empty.

        Args:
            agent: The agent instance this capability is executing against.
            task: The task record that tracks the execution lifecycle and event stream.
        """
        self.agent_file_manager_service = AgentFileManagerService(agent=agent)
        self.environment = SimpleNamespace()
        self.channels: dict[str, ChannelBuffer] = {
            channel_name: ChannelBuffer(maximum_memory_size=CHANNEL_BUFFER_MEMORY_LIMIT)
            for channel_name in type(self).channels
        }
        super().__init__(agent=agent, task=task)

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "name"):
            raise MissingAgentCapabilityConfigurationParameterError(
                parameter_name="name",
                # Since the agent template cannot be identified by name we identify
                # it by the filepath it was declared in.
                agent_capability_filepath=resolve_component_filepath(cls),
            )

        cls.options = cls.options or set()
        cls.supported_oses = cls.supported_oses or {SupportedOS.ANY}
        cls.authors = cls.authors or set()
        cls.mitre_attack_techniques = cls.mitre_attack_techniques or set()
        # A capability subclassing another capability inherits the name-keyed dict this
        # hook already built for the parent, so the declarations are taken back off it
        # before the set is validated and rebuilt below.
        if isinstance(cls.channels, dict):
            cls.channels = set(cls.channels.values())
        cls.channels = cls.channels or set()
        cls.services = construct_services_dataclass(server_singletons=server_singletons)
        try:
            _BaseAgentCapabilityModel(
                name=cls.name,
                description=cls.description,
                options=cls.options,
                authors=cls.authors,
                requires_admin=cls.requires_admin,
                supported_oses=cls.supported_oses,
                mitre_attack_techniques=cls.mitre_attack_techniques,
                validating_function=cls.validating_function,
                channels=cls.channels,
            )
        except ValidationError as exc:
            parameter_name, parameter_type = resolve_validation_error_parameter(
                exc=exc,
                parameter_types=get_type_hints(_BaseAgentCapabilityModel),
            )
            raise InvalidAgentCapabilityConfigurationParameterTypeError(
                agent_capability_str=resolve_component_filepath(cls),
                parameter_name=parameter_name,
                parameter_type=parameter_type,
            ) from None

        if not cls.name:
            raise EmptyAgentCapabilityNameError(
                agent_capability_filepath=resolve_component_filepath(cls),
            )
        # Normalize supported OSes to enum values if any valid supported OSes are
        # provided as strings. Otherwise, leave as is to allow for declaration of
        # custom/niche OSes.
        for os in cls.supported_oses:
            if isinstance(os, str):
                if os.lower() in SupportedOS:
                    cls.supported_oses.remove(os)
                    cls.supported_oses.add(SupportedOS(os.lower()))
        option_names = []
        for option in cls.options:
            if option.name in option_names:
                raise DuplicateAgentCapabilityOptionNameError(
                    option_name=option.name,
                    agent_capability_name=cls.name,
                )
            option_names.append(option.name)
        # Check that signature of function is minimally valid.
        if cls.validating_function:
            function_signature = signature(cls.validating_function)
            if len(function_signature.parameters) != 1:
                raise InvalidAgentCapabilityConfigurationParameterTypeError(
                    agent_capability_str=cls.name,
                    parameter_name="validating_function",
                    parameter_type=get_type_hints(cls)["validating_function"],
                )
            # We need to convert the validating function to a static method so that the
            # validating function class attribute is considered as just an ordinary
            # function rather than an actual method of the listener template.
            cls.validating_function = staticmethod(cls.validating_function)

        # For convenience purposes when providing the arguments of a particular
        # capability they are declared at the class level in a set (which also
        # implicitly helps prevent duplicate arguments). But when we want to interact
        # programmatically with the capability it is better to provide a dict like
        # interface hence the redeclaration of the class option here.
        # TODO: Find some way to redeclare the typing of this to allow it to play nice
        #  with IDE type suggestions.
        options = {}
        for option in cls.options:
            options[option.name] = option
        cls.options = options

        # Channels get the same set -> name-keyed dict treatment as options, and for the
        # same reason: declared as a set so duplicates are awkward to write, used as a
        # mapping because every reader of a channel has its name and not its declaration.
        channels = {}
        for channel in cls.channels:
            if channel.name in channels:
                raise DuplicateAgentCapabilityChannelNameError(
                    channel_name=channel.name,
                    agent_capability_name=cls.name,
                )
            channels[channel.name] = channel
        cls.channels = channels

        # Convert mitre attack technique IDs to a list of resolved
        # `MitreAttackTechnique` objects
        cls.mitre_attack_techniques = [
            resolve_mitre_attack_technique_id(mitre_attack_technique_id=technique_id)
            for technique_id in cls.mitre_attack_techniques
        ]

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"AgentCapability("
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"authors={self.authors!r}, "
            f"requires_admin={self.requires_admin!r}, "
            f"supported_oses={self.supported_oses!r}, "
            f"mitre_attack_techniques={self.mitre_attack_techniques!r}, "
            f"options={self.options!r}, "
            f"validating_function={self.validating_function!r}"
            f")"
        )

    @property
    def logger(self):
        """System logger for reporting this capability's execution as it runs.

        Returns:
            The system logger shared with the owning task.
        """
        return self.task.logger

    @property
    def event_logger(self):
        """Event logger for reporting this capability's execution as it runs.

        Shared with the owning task, so events recorded here (success, failure, info,
        warning, error, artifact, and progress updates) appear in the task's event log
        and are surfaced to the client. Entries are also mirrored to the task's system
        logger.

        Returns:
            The event logger shared with the owning task.
        """
        return self.task.event_logger

    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel:
        """Hook called before the task message is transmitted to the agent.

        Override to mutate or enrich the launch message prior to sending. This must
        return a TaskLaunchMessageModel. To deny the launch (for example when a
        pre-launch validation check fails) raise AgentCapabilityLaunchError; the task
        is then reported as ERRORED. Returning anything else is a contract violation
        rather than a denial and is reported as a fatal error against the capability.

        Args:
            task_launch_message: The task launch message prepared by the caller, containing
                the command, arguments, data, and any attached payload.

        Returns:
            The (possibly modified) task message to send.
        """
        return task_launch_message

    async def on_execute(self) -> Success | Failure | None:
        """Hook called after the task message has been sent to process the agent's response.

        Override to implement custom response handling logic. The default implementation
        waits for a single reply from the agent and wraps it in a Success or Failure.

        Returns:
            A Success wrapping the agent's response on success, a Failure on failure,
            or None if no response is expected.
        """
        return (await self.recv_from_agent()).to_outcome()

    async def execute(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> Success | Failure | None:
        """Dispatch the task to the agent and return the execution outcome.

        Calls on_launch to allow pre-send mutation, transmits the (possibly modified)
        message to the agent, then calls on_execute to await and process the response.

        Args:
            task_launch_message: The fully populated task launch message to dispatch,
                including the command, arguments, data, and any binary payload.

        Returns:
            The outcome from on_execute. Return Success or Failure to opt in to an
            explicit terminal event and task transition; return None when the capability
            reported everything it needs to through the event logger, in which case the
            task is assumed to have completed normally.

        Raises:
            AgentCapabilityLaunchError: If on_launch denies the launch by raising it. The
                task handler converts this into an ERRORED task.
            AgentCapabilityFatalError: If an unexpected exception escapes on_launch, the
                dispatch of the launch message or on_execute, or if on_launch returns
                anything other than a TaskLaunchMessageModel. The phase identifies which
                of those stages failed.
        """
        try:
            self.task_launch_message = task_launch_message.model_copy(deep=True)

            # LAUNCH: translate an unexpected exception from on_launch into a phase-tagged
            # fatal error. A deliberate AgentCapabilityLaunchError (a BaseSignalException)
            # is passed through untouched so the task handler still reports it as a launch
            # denial rather than a framework defect.
            try:
                modified_task_launch_message = await self.on_launch(task_launch_message)
            except asyncio.CancelledError:
                raise
            except BaseSignalException:
                raise
            except Exception as exc:
                raise AgentCapabilityFatalError(
                    agent_capability_name=self.name,
                    phase=AgentCapabilityPhase.LAUNCH,
                    underlying_exception=exc,
                ) from exc

            if not isinstance(modified_task_launch_message, TaskLaunchMessageModel):
                # Returning anything else breaks the hook's contract rather than
                # deliberately denying the launch, which is what raising
                # AgentCapabilityLaunchError is for, so it is classified as a launch phase
                # defect exactly like an exception escaping the hook. There is no
                # underlying exception to carry, so the contract violation is described as
                # the TypeError it amounts to.
                raise AgentCapabilityFatalError(
                    agent_capability_name=self.name,
                    phase=AgentCapabilityPhase.LAUNCH,
                    underlying_exception=TypeError(
                        "`on_launch` must return a `TaskLaunchMessageModel`, or raise "
                        "`AgentCapabilityLaunchError` to deny the launch, but it returned "
                        f"`{type(modified_task_launch_message).__name__}`."
                    ),
                )

            # DISPATCH: an unexpected failure putting the launch message on the outbox is
            # infrastructure, not the capability's deliberate failure path, so tag it.
            try:
                await self._task_messages_outbox.put(
                    task_message=modified_task_launch_message
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                raise AgentCapabilityFatalError(
                    agent_capability_name=self.name,
                    phase=AgentCapabilityPhase.DISPATCH,
                    underlying_exception=exc,
                ) from exc

            # EXECUTION: translate an unexpected exception from on_execute into a fatal
            # error while letting a deliberate AgentCapabilityExecutionError pass through.
            try:
                return await self.on_execute()
            except asyncio.CancelledError:
                raise
            except BaseSignalException:
                raise
            except Exception as exc:
                raise AgentCapabilityFatalError(
                    agent_capability_name=self.name,
                    phase=AgentCapabilityPhase.EXECUTION,
                    underlying_exception=exc,
                ) from exc
        finally:
            await self._shutdown_task_queues()

    async def _shutdown_task_queues(self) -> None:
        # Signal end of stream on both queues so any reader still waiting on the outbox is
        # informed the capability has finished and won't wait forever. `on_execute()` can
        # return before the outbox is drained (for example a capability that fires messages
        # without waiting for responses), so we shut down gracefully (`immediate=False`) to
        # let buffered outbound messages flush before readers see the end of stream
        # `END_OF_STREAM`.
        #
        # The channel buffers are shut down for the same reason and on the same terms: a
        # pump parked in `channel.get()` is released with `END_OF_STREAM`, and whatever is
        # still buffered stays readable so a client draining a channel sees the last bytes
        # the capability wrote rather than losing them to teardown.
        #
        # Every buffer is shut down even if an earlier one fails, so one failing does not
        # leave another's readers hanging. A failure is logged rather than raised: raising
        # would either displace the error already unwinding out of a hook or report a task
        # that ran fine as ERRORED, and readers of a buffer that was not shut down hang
        # either way, so it would only trade a truthful outcome for a misleading one.
        for shutdown in (
            self._task_messages_inbox.shutdown,
            self._task_messages_outbox.shutdown,
            *(channel.shutdown for channel in self.channels.values()),
        ):
            try:
                await shutdown(immediate=False)
            except asyncio.CancelledError:
                raise
            except Exception as cleanup_exc:
                self.logger.critical(
                    "Agent capability '{}' failed to shut down a task buffer. Any reader "
                    "waiting on that buffer will not observe the end of the stream. "
                    "{}: {}",
                    self.name,
                    type(cleanup_exc).__name__,
                    cleanup_exc,
                )

    @classmethod
    def to_json(cls) -> dict[str, Any]:
        """Serialize the capability's class-level metadata to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the capability name, description, authors, options
            (with their validation schemas), declared channels, MITRE ATT&CK techniques,
            supported OSes, admin requirement flag, and any validating function
            documentation.
        """
        return {
            "name": cls.name,
            "description": cls.description,
            "authors": list(cls.authors),
            "requires_admin": cls.requires_admin,
            "supported_oses": [str(os) for os in cls.supported_oses],
            "mitre_attack_techniques": [
                technique.model_dump(mode="json")
                for technique in cls.mitre_attack_techniques
            ],
            "options": {
                option_name: option.to_json()
                for option_name, option in cls.options.items()
            },
            "channels": {
                channel_name: channel.to_json()
                for channel_name, channel in cls.channels.items()
            },
            "validating_function": format_docstring_to_single_line(
                cls.validating_function.__doc__,
            )
            if cls.validating_function and cls.validating_function.__doc__
            else None,
        }
