from typing import Any

from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as comp_excs,
)
from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class AgentGeneratorsError(BaseConsortiumError):
    code = "AGENT_GENERATORS_ERROR"


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


class AgentGeneratorOverridesFinalMethodError(AgentGeneratorConfigurationError):
    code = "AGENT_GENERATOR_OVERRIDES_FINAL_METHOD_ERROR"

    def __init__(self, agent_generator_filepath: str, method_name: str) -> None:
        self.agent_generator_filepath = agent_generator_filepath
        self.method_name = method_name
        super().__init__(
            f"Failed to configure the agent generator defined at "
            f"'{agent_generator_filepath}'. The provided implementation overrides "
            f"`{method_name}()`, which is `final` and must not be overridden."
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


class MissingAgentGeneratorBuildStepConfigurationParameterError(
    AgentGeneratorConfigurationError,
):
    code = "MISSING_AGENT_GENERATOR_BUILD_STEP_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, parameter_name: str, agent_generator_build_step_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the agent generator build step defined at "
                f"'{agent_generator_build_step_filepath}'. The required parameter "
                f"'{parameter_name}' was not declared in the agent generator build "
                f"step's definition."
            ),
        )


class AgentGeneratorBuildStepOverridesFinalMethodError(
    AgentGeneratorConfigurationError
):
    code = "AGENT_GENERATOR_BUILD_STEP_OVERRIDES_FINAL_METHOD_ERROR"

    def __init__(
        self, agent_generator_build_step_filepath: str, method_name: str
    ) -> None:
        self.agent_generator_build_step_filepath = agent_generator_build_step_filepath
        self.method_name = method_name
        super().__init__(
            f"Failed to configure the agent generator build step defined at "
            f"'{agent_generator_build_step_filepath}'. The provided implementation "
            f"overrides `{method_name}()`, which is `final` and must not be overridden."
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


class AgentGeneratorOperationError(
    comp_excs.ComponentOperationError,
    AgentGeneratorsFrameworkError,
):
    """
    Base exception for all errors that occur during the operation of a particular
    agent generator.
    """

    code = "AGENT_GENERATOR_OPERATION_ERROR"

    _COMPONENT_TYPE = "agent generator"


class AgentGeneratorStartError(
    comp_excs.ComponentStartError, AgentGeneratorOperationError
):
    code = "AGENT_GENERATOR_START_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            component_str=agent_generator_str,
            error_message=error_message,
            detail=detail,
        )


class AgentGeneratorRuntimeError(
    comp_excs.ComponentRuntimeError, AgentGeneratorOperationError
):
    code = "AGENT_GENERATOR_RUNTIME_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            component_str=agent_generator_str,
            error_message=error_message,
            detail=detail,
        )


class AgentGeneratorBuildStepRuntimeError(
    comp_excs.ComponentRuntimeError,
    AgentGeneratorOperationError,
):
    code = "AGENT_GENERATOR_BUILD_STEP_RUNTIME_ERROR"
    _COMPONENT_TYPE = "agent generator build step"

    def __init__(
        self,
        agent_generator_build_step_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            component_str=agent_generator_build_step_str,
            error_message=error_message,
            detail=detail,
        )


class AgentGeneratorStopError(
    comp_excs.ComponentStopError, AgentGeneratorOperationError
):
    code = "AGENT_GENERATOR_STOP_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            component_str=agent_generator_str,
            error_message=error_message,
            detail=detail,
        )


class AgentGeneratorStateError(
    AgentGeneratorsFrameworkError,
    comp_excs.ComponentStateError,
):
    """
    Base exception for all errors that occur due to invalid status transitions or
    operations performed on an agent generator in an invalid status.
    """

    code = "AGENT_GENERATOR_STATE_ERROR"

    _COMPONENT_TYPE = "agent generator"


class AgentGeneratorNotRunningError(
    comp_excs.ComponentNotRunningError, AgentGeneratorStateError
):
    code = "AGENT_GENERATOR_NOT_RUNNING_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
    ):
        super().__init__(component_str=agent_generator_str)


class AgentGeneratorAlreadyRunningError(
    comp_excs.ComponentAlreadyRunningError, AgentGeneratorStateError
):
    code = "AGENT_GENERATOR_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
    ):
        super().__init__(component_str=agent_generator_str)


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
