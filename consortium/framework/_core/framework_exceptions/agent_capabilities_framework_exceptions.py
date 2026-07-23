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
