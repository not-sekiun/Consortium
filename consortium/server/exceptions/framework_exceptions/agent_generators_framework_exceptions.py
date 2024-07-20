"""
Exception hierarchy for agents framework:

- BaseFrameworkException: Base class for all framework exceptions.
  - AgentGeneratorsFrameworkError: General error occurred in the agent generators
  framework.
    - AgentGeneratorConfigurationError: Error occurred during agent generator
    configuration.
      - AgentGeneratorConfigurationParameterTypeError: Invalid type for an agent
      generator configuration parameter.
      - RequiredAgentGeneratorConfigurationParameterNotDeclaredError: Required
      parameter not declared in agent generator configuration.
    - AgentGeneratorBuildStepConfigurationError: Error occurred during agent generator
    build step configuration.
      - AgentGeneratorBuildStepConfigurationParameterTypeError: Invalid type for a
      build step configuration parameter.
      - RequiredAgentGeneratorBuildStepConfigurationParameterNotDeclaredError:
      Required parameter not declared in build step configuration.
      - EmptyAgentGeneratorBuildStepNameError: The name provided for an agent generator
      build step is an empty string.
    - AgentGeneratorCreationError: Error occurred during agent generator creation.
      - AgentGeneratorCreationParameterTypeError: Invalid type for an agent generator
      creation parameter.
      - EmptyAgentGeneratorNameError: The name provided for an agent generator is an
      empty string.
    - AgentGeneratorNotRunningError: An error occurred because the requested operation
    could not be completed while the agent generator is not running.
    - AgentGeneratorAlreadyRunningError: An error occurred because the requested
    operation could not be completed while the agent generator is running.
    - AgentGeneratorStartError: Error occurred while attempting to start an agent
    generator.
    - AgentGeneratorBuildError: Error occurred while attempting to build an agent.
    - AgentGeneratorBuildStepError: Error occurred during agent generator build step.
    - AgentGeneratorStopError: Error occurred while attempting to stop an agent.
"""

from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class AgentGeneratorsFrameworkError(BaseFrameworkException):
    pass


class AgentGeneratorConfigurationError(AgentGeneratorsFrameworkError):
    pass


class AgentGeneratorConfigurationParameterTypeError(AgentGeneratorConfigurationError):
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


class RequiredAgentGeneratorConfigurationParameterNotDeclaredError(
    AgentGeneratorConfigurationError,
):
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
    pass


class AgentGeneratorBuildStepConfigurationParameterTypeError(
    AgentGeneratorBuildStepConfigurationError,
):
    def __init__(
        self,
        agent_generator_build_step_name: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure the agent generator build step "
                    f"'{agent_generator_build_step_name}'. The parameter "
                    f"'{parameter_name}' must be of type '{parameter_type}' in the "
                    f"build step's definition."
                ),
            )
        else:
            super().__init__(message=error_message)


class RequiredAgentGeneratorBuildStepConfigurationParameterNotDeclaredError(
    AgentGeneratorBuildStepConfigurationError,
):
    def __init__(self, parameter_name: str, agent_generator_build_step_name: str):
        super().__init__(
            message=(
                f"Failed to configure the agent generator build step "
                f"'{agent_generator_build_step_name}'. The required parameter "
                f"'{parameter_name}' was not declared in the agent generator build "
                f"step's definition."
            ),
        )


class AgentGeneratorCreationError(AgentGeneratorsFrameworkError):
    pass


class AgentGeneratorCreationParameterTypeError(AgentGeneratorCreationError):
    def __init__(
        self,
        agent_generator: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to create the agent generator '{agent_generator}'. "
                    f"The parameter '{parameter_name}' must be of type '{parameter_type}' "
                    "in the agent generator's provided parameters."
                ),
            )
        else:
            super().__init__(message=error_message)


class EmptyAgentGeneratorNameError(AgentGeneratorCreationError):
    def __init__(self, agent_generator_filepath: str):
        super().__init__(
            message=(
                f"Failed to create the agent generator defined at "
                f"'{agent_generator_filepath}'. The name provided in the agent "
                "generator's parameters during creation cannot be empty."
            ),
        )


class EmptyAgentGeneratorBuildStepNameError(AgentGeneratorBuildStepConfigurationError):
    def __init__(self, agent_generator_build_step_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the agent generator build step defined at "
                f"'{agent_generator_build_step_filepath}'. The name of the build step "
                "was empty in its definition."
            ),
        )


class AgentGeneratorNotRunningError(AgentGeneratorsFrameworkError):
    def __init__(
        self,
        agent_generator: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"An error occurred with the agent generator "
                f"'{agent_generator}' because it is not running. "
                f"{error_message}"
            ),
        )


class AgentGeneratorAlreadyRunningError(AgentGeneratorsFrameworkError):
    def __init__(
        self,
        agent_generator: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"An error occurred with the agent generator "
                f"'{agent_generator}' because it is already running. "
                f"{error_message}"
            ),
        )


class AgentGeneratorStartError(AgentGeneratorsFrameworkError):
    def __init__(
        self,
        agent_generator: str,
        start_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"Failed to start the agent generator '{agent_generator}'. "
                f"{start_error_message}"
            ),
            detail=detail,
        )


class AgentGeneratorBuildError(AgentGeneratorsFrameworkError):
    def __init__(
        self,
        agent_generator: str,
        build_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"Failed to build an agent with the agent generator "
                f"'{agent_generator}'. {build_error_message}"
            ),
            detail=detail,
        )


class AgentGeneratorBuildStepError(AgentGeneratorsFrameworkError):
    def __init__(
        self,
        agent_generator_build_step: str,
        build_step_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"An error occurred during the agent generator build step "
                f"'{agent_generator_build_step}'. {build_step_error_message}"
            ),
            detail=detail,
        )


class AgentGeneratorStopError(AgentGeneratorsFrameworkError):
    def __init__(
        self,
        agent_generator: str,
        stop_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"Failed to stop the agent generator '{agent_generator}'. "
                f"{stop_error_message}"
            ),
            detail=detail,
        )
