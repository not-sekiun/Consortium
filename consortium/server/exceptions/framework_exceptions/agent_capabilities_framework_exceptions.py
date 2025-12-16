from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class AgentCapabilitiesFrameworkError(BaseFrameworkException):
    code = "AGENT_CAPABILITIES_FRAMEWORK_ERROR"


class AgentCapabilityConfigurationError(AgentCapabilitiesFrameworkError):
    code = "AGENT_CAPABILITY_CONFIGURATION_ERROR"


class InvalidAgentCapabilityConfigurationParameterTypeError(
    AgentCapabilityConfigurationError,
):
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
    code = "EMPTY_AGENT_CAPABILITY_NAME_ERROR"

    def __init__(self, agent_capability_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability defined at "
                f"'{agent_capability_filepath}'. The name provided in the agent "
                f"template's definition during configuration cannot be empty."
            ),
        )


class DuplicateAgentCapabilityOptionNameError(AgentCapabilitiesFrameworkError):
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
    code = "CUSTOM_OS_STRING_ALREADY_REGISTERED_ERROR"

    def __init__(self, custom_os_str: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability. The custom OS string "
                f"provided '{custom_os_str}' has already been registered."
            ),
        )
