from typing import Any

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class AgentGeneratorsError(BaseConsortiumError):
    code = "AGENT_GENERATORS_ERROR"


class AgentGeneratorsServiceError(AgentGeneratorsError):
    code = "AGENT_GENERATORS_SERVICE_ERROR"


class AgentGeneratorNotFoundError(AgentGeneratorsServiceError):
    code = "AGENT_GENERATOR_NOT_FOUND_ERROR"

    def __init__(self, agent_generator_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent generator. No agent generator was "
                f"found with the provided agent generator ID '{agent_generator_id}'."
            ),
        )


class AgentGeneratorAlreadyExistsError(AgentGeneratorsServiceError):
    code = "AGENT_GENERATOR_ALREADY_EXISTS_ERROR"

    def __init__(self, agent_generator_id: str):
        super().__init__(
            message=(
                f"Failed to add the specified agent generator. An agent generator "
                f"already exists with the agent generator ID '{agent_generator_id}'."
            ),
        )


class AgentGeneratorParameterUpdateError(AgentGeneratorsServiceError):
    code = "AGENT_GENERATOR_PARAMETER_UPDATE_ERROR"


class InvalidAgentGeneratorParameterNameError(AgentGeneratorParameterUpdateError):
    code = "INVALID_AGENT_GENERATOR_PARAMETER_NAME_ERROR"

    def __init__(self, agent_generator: str, parameter_name: str):
        super().__init__(
            message=(
                f"Failed to update the agent generator parameter for agent generator "
                f"'{agent_generator}'. The provided parameter name '{parameter_name}' "
                f"was not found for the agent generator."
            ),
        )


class InvalidAgentGeneratorParameterValueError(AgentGeneratorParameterUpdateError):
    code = "INVALID_AGENT_GENERATOR_PARAMETER_VALUE_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        parameter_name: str,
        parameter_value: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to update the agent generator parameter for agent generator "
                f"'{agent_generator_str}'. The value provided '{parameter_value}' for "
                f"the parameter '{parameter_name}' is invalid. {error_message}"
            ),
        )


class AgentGeneratorsFrameworkError(AgentGeneratorsError):
    code = "AGENT_GENERATORS_FRAMEWORK_ERROR"


class AgentGeneratorConfigurationError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_CONFIGURATION_ERROR"


class AgentGeneratorConfigurationParameterTypeError(AgentGeneratorConfigurationError):
    code = "AGENT_GENERATOR_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        agent_generator_filepath: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to configure the agent generator defined at "
                f"'{agent_generator_filepath}'. The parameter '{parameter_name}' must "
                f"be of type '{parameter_type}' in the agent generator's definition."
            )
        )


class MissingAgentGeneratorConfigurationParameterError(
    AgentGeneratorConfigurationError,
):
    code = "MISSING_AGENT_GENERATOR_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, parameter_name: str, agent_generator_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the agent generator defined at "
                f"'{agent_generator_filepath}'. The required parameter "
                f"'{parameter_name}' was not declared in the agent generator's "
                f"definition."
            ),
        )


class AgentGeneratorBuildStepConfigurationError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_BUILD_STEP_CONFIGURATION_ERROR"


class AgentGeneratorBuildStepConfigurationParameterTypeError(
    AgentGeneratorBuildStepConfigurationError,
):
    code = "AGENT_GENERATOR_BUILD_STEP_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        agent_generator_build_step_str: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure the agent generator build step "
                    f"'{agent_generator_build_step_str}'. The parameter "
                    f"'{parameter_name}' must be of type '{parameter_type}' in the "
                    f"build step's definition."
                ),
            )
        else:
            super().__init__(message=error_message)


class RequiredAgentGeneratorBuildStepConfigurationParameterNotDeclaredError(
    AgentGeneratorBuildStepConfigurationError,
):
    code = (
        "REQUIRED_AGENT_GENERATOR_BUILD_STEP_CONFIGURATION_PARAMETER_NOT_DECLARED_ERROR"
    )

    def __init__(self, agent_generator_build_step_str: str, parameter_name: str):
        super().__init__(
            message=(
                f"Failed to configure the agent generator build step "
                f"'{agent_generator_build_step_str}'. The required parameter "
                f"'{parameter_name}' was not declared in the agent generator build "
                f"step's definition."
            ),
        )


class AgentGeneratorCreationError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_CREATION_ERROR"


class AgentGeneratorCreationParameterTypeError(AgentGeneratorCreationError):
    code = "AGENT_GENERATOR_CREATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to create the agent generator '{agent_generator_str}'. "
                    f"The parameter '{parameter_name}' must be of type '{parameter_type}' "
                    "in the agent generator's provided parameters."
                ),
            )
        else:
            super().__init__(message=error_message)


class EmptyAgentGeneratorBuildStepNameError(AgentGeneratorBuildStepConfigurationError):
    code = "EMPTY_AGENT_GENERATOR_BUILD_STEP_NAME_ERROR"

    def __init__(self, agent_generator_build_step_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the agent generator build step defined at "
                f"'{agent_generator_build_step_filepath}'. The name of the build step "
                "was empty in its definition."
            ),
        )


class AgentGeneratorNotRunningError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_NOT_RUNNING_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
    ):
        super().__init__(
            message=(
                f"Failed to perform the requested operation on the agent generator "
                f"'{agent_generator_str}'. The agent generator is not running which "
                f"conflicts with the operation that was requested."
            ),
        )


class AgentGeneratorAlreadyRunningError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
    ):
        super().__init__(
            message=(
                f"Failed to perform the requested operation on the agent generator "
                f"'{agent_generator_str}'. The agent generator is already running "
                f"which conflicts with the operation that was requested."
            ),
        )


class AgentGeneratorStartError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_START_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"Failed to start the agent generator '{agent_generator_str}'. "
                f"{error_message}"
            ),
            detail=detail,
        )


class AgentGeneratorBuildError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_BUILD_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"Failed to build an agent with the agent generator "
                f"'{agent_generator_str}'. {error_message}"
            ),
            detail=detail,
        )


class AgentGeneratorBuildStepError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_BUILD_STEP_ERROR"

    def __init__(
        self,
        agent_generator_build_step_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"An error occurred during the agent generator build step "
                f"'{agent_generator_build_step_str}'. {error_message}"
            ),
            detail=detail,
        )


class AgentGeneratorStopError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_STOP_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"Failed to stop the agent generator '{agent_generator_str}'. "
                f"{error_message}"
            ),
            detail=detail,
        )
