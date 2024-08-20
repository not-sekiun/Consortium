from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class AgentCapabilitiesFrameworkError(BaseFrameworkException):
    pass


class AgentCapabilityConfigurationParameterError(AgentCapabilitiesFrameworkError):
    pass


class AgentCapabilityConfigurationParameterTypeError(
    AgentCapabilityConfigurationParameterError,
):
    def __init__(
        self,
        agent_capability: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure the agent capability '{agent_capability}'. "
                    f"The parameter '{parameter_name}' must be of type "
                    f"'{parameter_type}' in the agent capability's definition."
                ),
            )
        else:
            super().__init__(
                message=(
                    f"Failed to configure the agent capability '{agent_capability}'. "
                    f"{error_message}"
                ),
            )


class RequiredAgentCapabilityConfigurationParameterNotDeclaredError(
    AgentCapabilityConfigurationParameterError,
):
    def __init__(self, parameter_name: str, agent_capability: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability '{agent_capability}'. "
                f"The required parameter '{parameter_name}' was not declared in the "
                f"agent capability's definition."
            ),
        )


class EmptyAgentCapabilityNameError(AgentCapabilitiesFrameworkError):
    def __init__(self, agent_capability_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability defined at "
                f"'{agent_capability_filepath}'. The name provided in the agent "
                f"template's definition during configuration cannot be empty."
            ),
        )


class DuplicateAgentCapabilityArgumentNameError(AgentCapabilitiesFrameworkError):
    def __init__(self, argument_name: str, agent_capability: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability {agent_capability}'. The "
                f"arguments provided to the agent capability must not have duplicate "
                f"names but the name '{argument_name}' was duplicated."
            ),
        )


class CustomOSStringAlreadyRegisteredError(AgentCapabilitiesFrameworkError):
    def __init__(self, custom_os_string: str):
        super().__init__(
            message=(
                f"Failed to configure the agent capability. The custom OS string "
                f"provided '{custom_os_string}' has already been registered."
            ),
        )
