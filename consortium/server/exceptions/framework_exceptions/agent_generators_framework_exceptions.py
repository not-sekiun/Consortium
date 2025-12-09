# """
# Exception hierarchy for agents framework:
#
# - BaseFrameworkException: Base class for all framework exceptions.
#   - AgentGeneratorsFrameworkError: General error occurred in the agent generators
#   framework.
#     - AgentGeneratorConfigurationError: Error occurred during agent generator
#     configuration.
#       - AgentGeneratorConfigurationParameterTypeError: Invalid type for an agent
#       generator configuration parameter.
#       - RequiredAgentGeneratorConfigurationParameterNotDeclaredError: Required
#       parameter not declared in agent generator configuration.
#     - AgentGeneratorBuildStepConfigurationError: Error occurred during agent generator
#     build step configuration.
#       - AgentGeneratorBuildStepConfigurationParameterTypeError: Invalid type for a
#       build step configuration parameter.
#       - RequiredAgentGeneratorBuildStepConfigurationParameterNotDeclaredError:
#       Required parameter not declared in build step configuration.
#       - EmptyAgentGeneratorBuildStepNameError: The name provided for an agent generator
#       build step is an empty string.
#     - AgentGeneratorCreationError: Error occurred during agent generator creation.
#       - AgentGeneratorCreationParameterTypeError: Invalid type for an agent generator
#       creation parameter.
#     - AgentGeneratorNotRunningError: An error occurred because the requested operation
#     could not be completed while the agent generator is not running.
#     - AgentGeneratorAlreadyRunningError: An error occurred because the requested
#     operation could not be completed while the agent generator is running.
#     - AgentGeneratorStartError: Error occurred while attempting to start an agent
#     generator.
#     - AgentGeneratorBuildError: Error occurred while attempting to build an agent.
#     - AgentGeneratorBuildStepError: Error occurred during agent generator build step.
#     - AgentGeneratorStopError: Error occurred while attempting to stop an agent.
# """

from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class AgentGeneratorsFrameworkError(BaseFrameworkException):
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
        error_message: str = "",
    ):
        if not error_message:
            error_message = (
                f"Failed to configure the agent generator defined at "
                f"'{agent_generator_filepath}'. The parameter '{parameter_name}' must "
                f"be of type '{parameter_type}' in the agent generator's definition."
            )
        super().__init__(message=error_message)


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
        error_message: str,
    ):
        super().__init__(
            message=(
                f"An error occurred with the agent generator "
                f"'{agent_generator_str}' because it is not running. "
                f"{error_message}"
            ),
        )


class AgentGeneratorAlreadyRunningError(AgentGeneratorsFrameworkError):
    code = "AGENT_GENERATOR_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"An error occurred with the agent generator "
                f"'{agent_generator_str}' because it is already running. "
                f"{error_message}"
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
