from pydantic.config import JsonValue

from consortium.framework._core.framework_exceptions.base_framework_exception import (
    BaseFrameworkError,
)


class AgentCapabilitiesFrameworkError(BaseFrameworkError):
    """Base exception for all errors that occur within the agent capabilities framework."""

    code = "AGENT_CAPABILITIES_FRAMEWORK_ERROR"


class AgentCapabilityConfigurationError(AgentCapabilitiesFrameworkError):
    """Base exception for all errors that occur during the configuration of a particular
    agent capability.
    """

    code = "AGENT_CAPABILITY_CONFIGURATION_ERROR"


class InvalidAgentCapabilityConfigurationParameterTypeError(
    AgentCapabilityConfigurationError,
):
    """Raised when an agent capability's configuration parameter is not of the expected
    type during agent capability configuration.
    """

    code = "INVALID_AGENT_CAPABILITY_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        agent_capability_str: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to configure the agent capability "
                f"'{agent_capability_str}'. The parameter '{parameter_name}' "
                f"must be of type '{parameter_type}' in the agent capability's "
                f"definition."
            ),
        )


class MissingAgentCapabilityConfigurationParameterError(
    AgentCapabilityConfigurationError,
):
    """Raised when a required parameter is not declared in an agent capability's definition
    during agent capability configuration.
    """

    code = "MISSING_AGENT_CAPABILITY_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, agent_capability_filepath: str, parameter_name: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability "
                f"'{agent_capability_filepath}'. The required parameter "
                f"'{parameter_name}' was not declared in the agent capability's "
                f"definition."
            ),
        )


class EmptyAgentCapabilityNameError(AgentCapabilityConfigurationError):
    """Raised when an empty name is provided in an agent capability's definition during
    agent capability configuration.
    """

    code = "EMPTY_AGENT_CAPABILITY_NAME_ERROR"

    def __init__(self, agent_capability_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability defined at "
                f"'{agent_capability_filepath}'. The name provided in the agent "
                f"capability's definition during configuration cannot be empty."
            ),
        )


class DuplicateAgentCapabilityOptionNameError(AgentCapabilityConfigurationError):
    """Raised when duplicate option names are provided in an agent capability's definition
    during agent capability configuration.
    """

    code = "DUPLICATE_AGENT_CAPABILITY_OPTION_NAME_ERROR"

    def __init__(self, agent_capability_name: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability '{agent_capability_name}'. "
                f"The options provided to the agent capability must not have duplicate "
                f"names but the name '{option_name}' was duplicated."
            ),
        )


class InvalidAgentCapabilityChannelConfigurationParameterTypeError(
    AgentCapabilityConfigurationError,
):
    """Raised when a channel's configuration parameter is not of the expected type
    during agent capability configuration.
    """

    code = "INVALID_AGENT_CAPABILITY_CHANNEL_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(self, channel_str: str, parameter_name: str, parameter_type: str):
        super().__init__(
            message=(
                f"Failed to configure the channel '{channel_str}'. The parameter "
                f"'{parameter_name}' must be of type '{parameter_type}'."
            ),
        )


class EmptyAgentCapabilityChannelNameError(AgentCapabilityConfigurationError):
    """Raised when an empty channel name is provided during agent capability
    configuration.
    """

    code = "EMPTY_AGENT_CAPABILITY_CHANNEL_NAME_ERROR"

    def __init__(self):
        super().__init__(
            message=(
                "Failed to configure a channel. The name provided in the channel's "
                "declaration cannot be empty."
            ),
        )


class DuplicateAgentCapabilityChannelNameError(AgentCapabilityConfigurationError):
    """Raised when duplicate channel names are declared in an agent capability's
    definition during agent capability configuration.
    """

    code = "DUPLICATE_AGENT_CAPABILITY_CHANNEL_NAME_ERROR"

    def __init__(self, agent_capability_name: str, channel_name: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability '{agent_capability_name}'. "
                f"The channels declared by the agent capability must not have duplicate "
                f"names but the name '{channel_name}' was duplicated."
            ),
        )


class CustomOSStringAlreadyRegisteredError(AgentCapabilityConfigurationError):
    """Raised when the provided custom OS string has already been registered in the agent
    capabilities framework during agent capability configuration.
    """

    code = "CUSTOM_OS_STRING_ALREADY_REGISTERED_ERROR"

    def __init__(self, custom_os_str: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability. The custom OS string "
                f"provided '{custom_os_str}' has already been registered."
            ),
        )


class AgentCapabilityLaunchError(AgentCapabilitiesFrameworkError):
    """Raised when an agent capability is denied from launching.

    This is the launch-time analogue of `AgentCapabilityExecutionError`: it reports a
    task that never started because a pre-launch check (validation) failed, as opposed
    to a task that failed while running.
    """

    code = "AGENT_CAPABILITY_LAUNCH_ERROR"

    def __init__(
        self,
        agent_capability_name: str,
        error_message: str,
        detail: dict[str, JsonValue] | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to launch agent capability '{agent_capability_name}'. "
                f"{error_message}"
            ),
            detail=detail,
        )


class AgentCapabilityExecutionError(AgentCapabilitiesFrameworkError):
    """Raised when an agent capability encounters an error during its execution."""

    code = "AGENT_CAPABILITY_EXECUTION_ERROR"

    def __init__(
        self,
        agent_capability_name: str,
        error_message: str,
        detail: dict[str, JsonValue] | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to execute agent capability '{agent_capability_name}'. "
                f"{error_message}"
            ),
            detail=detail,
        )


class AgentCapabilityFatalError(AgentCapabilitiesFrameworkError):
    """Raised when an unexpected exception escapes an agent capability's hooks or its
    execution infrastructure, terminating the task fatally.

    This is the agent capability analogue of `ComponentFatalError`. Unlike
    `AgentCapabilityLaunchError` and `AgentCapabilityExecutionError`, which report the
    capability's deliberate, typed failure paths, this reports an unhandled exception that
    escaped `on_launch`, message dispatch, or `on_execute`. The `phase` identifies which of
    those stages failed. The original exception is preserved as the cause when this error
    is re-raised, so its traceback survives server side; only the type and message cross
    the API boundary through `detail`.
    """

    code = "AGENT_CAPABILITY_FATAL_ERROR"

    def __init__(
        self,
        agent_capability_name: str,
        phase: str,
        underlying_exception: Exception,
    ):
        error_type = type(underlying_exception).__name__
        error_message = str(underlying_exception)
        super().__init__(
            message=(
                f"Failed to run agent capability '{agent_capability_name}'. An "
                f"unhandled exception was raised during the {phase} phase. "
                # Rendered the way Python renders an exception on the final line of a
                # traceback. An exception carrying no message renders as its type alone,
                # since a trailing "TypeError: " reads as truncated output.
                + (f"{error_type}: {error_message}" if error_message else error_type)
            ),
            # `detail` is serialized to clients, so it carries only what a client can act
            # on. The traceback stays on `__cause__`, which never crosses the API boundary.
            detail={
                "type": error_type,
                "message": error_message,
                "phase": phase,
            },
        )


class AgentCapabilityTaskHandlerError(AgentCapabilitiesFrameworkError):
    """Raised when an unexpected exception escapes the task handler itself, outside the
    agent capability's execution contract.

    `AgentCapabilityFatalError` covers the stages the handler can attribute to a
    capability (`launch`, `dispatch`, `execution`), so it carries a `phase`. Reaching this
    error instead means the failure happened in the handler surrounding those stages,
    where no phase applies: it is a framework defect rather than a capability one. It is
    recorded on the task so the task does not sit non-terminal forever rather than being
    raised, so it carries no cause; the original exception's traceback is logged where it
    is caught.
    """

    code = "AGENT_CAPABILITY_TASK_HANDLER_ERROR"

    def __init__(
        self,
        agent_capability_name: str,
        underlying_exception: BaseException,
    ):
        error_type = type(underlying_exception).__name__
        error_message = str(underlying_exception)
        # Message and detail follow `AgentCapabilityFatalError` above, minus the phase.
        super().__init__(
            message=(
                f"Failed to run agent capability '{agent_capability_name}'. An unhandled "
                f"exception escaped the task handler. This is a framework defect, not a "
                f"failure reported by the capability. "
                + (f"{error_type}: {error_message}" if error_message else error_type)
            ),
            detail={
                "type": error_type,
                "message": error_message,
            },
        )


class PayloadTooLargeError(AgentCapabilitiesFrameworkError):
    """Raised when a payload being received exceeds a maximum size its transport set.

    The cap is opt in: `Payload.from_async_iterable` is uncapped by default and enforces
    a bound only when a caller passes `max_size`, in which case it is enforced as the
    source is consumed so an unbounded upload is rejected mid-stream rather than after
    being fully buffered. This is the single place transports learn a payload was refused
    for size, replacing the per-transport sentinels and cap loops each one used to carry.
    """

    code = "PAYLOAD_TOO_LARGE_ERROR"

    def __init__(self, max_size: int):
        super().__init__(
            message=(
                f"The payload exceeded the maximum allowed size of {max_size} bytes."
            ),
            detail={"max_size": max_size},
        )


class AgentCommunicationEndOfStreamError(AgentCapabilitiesFrameworkError):
    """Raised when a communicator reaches the end of a task's message stream.

    A communicator is coordinated with the remote endpoint for the lifetime of a task, so
    it should never observe end of stream while waiting for a message from the agent.
    Observing it means the inbox was shut down out from under a coordinated read, which is
    a genuine error rather than the normal termination signal the outbox-side readers rely
    on.
    """

    code = "AGENT_COMMUNICATION_END_OF_STREAM_ERROR"

    def __init__(
        self,
        agent_id: str,
        name: str,
        task_id: str,
        command: str,
    ):
        super().__init__(
            message=(
                f"Failed to receive message from agent '{name}' ({agent_id}). Reached "
                f"the end of the message stream for task '{command}' ({task_id}) "
                f"unexpectedly while waiting for a message from the agent."
            ),
        )
