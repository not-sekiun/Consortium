from typing import Any

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


class EmptyAgentCapabilityNameError(AgentCapabilitiesFrameworkError):
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


class DuplicateAgentCapabilityOptionNameError(AgentCapabilitiesFrameworkError):
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


class CustomOSStringAlreadyRegisteredError(AgentCapabilitiesFrameworkError):
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


class AgentCapabilityExecutionError(AgentCapabilitiesFrameworkError):
    code = "AGENT_CAPABILITY_EXECUTION_ERROR"

    def __init__(
        self, agent_capability_name: str, error_message: str, detail: Any = None
    ):
        super().__init__(
            message=(
                f"Failed to execute agent capability '{agent_capability_name}'. "
                f"{error_message}"
            ),
            detail=detail,
        )
