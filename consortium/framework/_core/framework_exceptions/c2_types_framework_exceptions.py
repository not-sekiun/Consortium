from consortium.framework._core.framework_exceptions.base_framework_exception import (
    BaseFrameworkError,
)


class C2TypesFrameworkError(BaseFrameworkError):
    """Base exception for all errors that occur within the C2 types framework."""

    code = "C2_TYPES_FRAMEWORK_ERROR"


class ListenerTypeConfigurationError(C2TypesFrameworkError):
    """Base exception for all errors that occur when a listener type fails to be configured."""

    code = "LISTENER_TYPE_CONFIGURATION_ERROR"


class ListenerTypeConfigurationParameterTypeError(ListenerTypeConfigurationError):
    """Raised when a provided listener type parameter is not of the expected type during
    listener type configuration.
    """

    code = "LISTENER_TYPE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        listener_type_filepath: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to configure the listener type defined at "
                f"'{listener_type_filepath}'. The parameter '{parameter_name}' "
                f"must be of type '{parameter_type}' in the listener type's "
                f"definition."
            ),
        )


class EmptyListenerTypeNameError(ListenerTypeConfigurationError):
    """Raised when an empty name is provided for a listener type during configuration."""

    code = "EMPTY_LISTENER_TYPE_NAME_ERROR"

    def __init__(self, listener_type_filepath: str):
        super().__init__(
            f"Failed to configure the listener type defined at "
            f"'{listener_type_filepath}'. The name provided in the listener type's "
            f"definition during configuration cannot be empty.",
        )


class AgentTypeConfigurationError(C2TypesFrameworkError):
    """Base exception for all errors that occur when an agent type fails to be configured."""

    code = "AGENT_TYPE_CONFIGURATION_ERROR"


class AgentTypeConfigurationParameterTypeError(AgentTypeConfigurationError):
    """Raised when a provided agent type parameter is not of the expected type during
    agent type configuration.
    """

    code = "AGENT_TYPE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        agent_type_filepath: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to configure the agent type defined at "
                f"'{agent_type_filepath}'. The parameter '{parameter_name}' "
                f"must be of type '{parameter_type}' in the agent type's "
                f"definition."
            ),
        )


class EmptyAgentTypeNameError(AgentTypeConfigurationError):
    """Raised when an empty name is provided for an agent type during configuration."""

    code = "EMPTY_AGENT_TYPE_NAME_ERROR"

    def __init__(self, agent_type_filepath: str):
        super().__init__(
            f"Failed to configure the agent type defined at "
            f"'{agent_type_filepath}'. The name provided in the agent type's "
            f"definition during configuration cannot be empty.",
        )


class DuplicateAgentCapabilityNameError(AgentTypeConfigurationError):
    """Raised when a duplicate name is provided in the set of defined agent
    capability's for a particular agent type"""

    code = "DUPLICATE_AGENT_CAPABILITY_NAME_ERROR"

    def __init__(
        self,
        agent_type_filepath: str,
        agent_capability_name: str,
    ):
        super().__init__(
            message=(
                f"Failed to configure the agent type defined at "
                f"'{agent_type_filepath}'. The agent type's set of defined agent "
                f"capabilities contains an agent capability with a non-unique name "
                f"'{agent_capability_name}'."
            ),
        )
