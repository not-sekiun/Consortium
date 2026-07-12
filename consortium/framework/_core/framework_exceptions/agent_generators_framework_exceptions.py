from pydantic import JsonValue

from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    ComponentAlreadyRunningError,
    ComponentNotRunningError,
    ComponentOperationError,
    ComponentRuntimeError,
    ComponentsFrameworkError,
    ComponentStartError,
    ComponentStateError,
    ComponentStopError,
)


class AgentGeneratorsFrameworkError(ComponentsFrameworkError):
    """Base exception for all errors that occur within the agent generators framework."""

    code = "AGENT_GENERATORS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "agent generator"


class AgentGeneratorConfigurationError(AgentGeneratorsFrameworkError):
    """Base exception for agent generator configuration errors."""

    code = "AGENT_GENERATOR_CONFIGURATION_ERROR"


class AgentGeneratorConfigurationParameterTypeError(AgentGeneratorConfigurationError):
    """Raised when an agent generator's configuration parameter is not of the expected
    type during agent generator configuration.
    """

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
    """Raised when a required parameter is not declared in an agent generator's definition
    during agent generator configuration.
    """

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


class DuplicateAgentGeneratorBuildStepNameError(AgentGeneratorConfigurationError):
    """Raised when a duplicate name is provided in the list of defined agent generator
    build steps for a particular agent generator.
    """

    code = "DUPLICATE_AGENT_GENERATOR_BUILD_STEP_NAME_ERROR"

    def __init__(
        self,
        agent_generator_filepath: str,
        agent_generator_build_step_name: str,
    ):
        super().__init__(
            message=(
                f"Failed to configure the agent generator defined at "
                f"'{agent_generator_filepath}'. The agent generator's list of defined "
                f"build steps contains a build step with a non-unique name "
                f"'{agent_generator_build_step_name}'."
            ),
        )


class AgentGeneratorOverridesFinalMethodError(AgentGeneratorConfigurationError):
    """Raised when an agent generator's implementation overrides a final method during
    agent generator configuration.
    """

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
    """Base exception for agent generator build step configuration errors."""

    code = "AGENT_GENERATOR_BUILD_STEP_CONFIGURATION_ERROR"


class AgentGeneratorBuildStepConfigurationParameterTypeError(
    AgentGeneratorBuildStepConfigurationError,
):
    """Raised when an agent generator build step's configuration parameter is not of the
    expected type during agent generator build step configuration.
    """

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
    """Raised when a required parameter is not declared in an agent generator build step's
    definition during agent generator build step configuration.
    """

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
    """Raised when a required parameter is not declared in an agent generator build step's
    definition during agent generator build step configuration.
    """

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
    """Raised when an agent generator build step's implementation overrides a final method
    during agent generator build step configuration.
    """

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
    """Base exception for agent generator creation errors."""

    code = "AGENT_GENERATOR_CREATION_ERROR"


class AgentGeneratorCreationParameterTypeError(AgentGeneratorCreationError):
    """Raised when a provided agent generator parameter is not of the expected type during
    agent generator creation.
    """

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
    """Raised when an empty name is provided in an agent generator build step's definition
    during agent generator build step configuration.
    """

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
    ComponentOperationError,
    AgentGeneratorsFrameworkError,
):
    """Base exception for all errors that occur during the operation of a particular
    agent generator.
    """

    code = "AGENT_GENERATOR_OPERATION_ERROR"


class AgentGeneratorStartError(ComponentStartError, AgentGeneratorOperationError):
    """Raised when an agent generator fails to start during agent generator operation."""

    code = "AGENT_GENERATOR_START_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: dict[str, JsonValue],
    ):
        super().__init__(
            component_str=agent_generator_str,
            error_message=error_message,
            detail=detail,
        )


class AgentGeneratorRuntimeError(ComponentRuntimeError, AgentGeneratorOperationError):
    """Raised when an agent generator encounters an unhandled error at runtime during
    agent generator operation.
    """

    code = "AGENT_GENERATOR_RUNTIME_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: dict[str, JsonValue],
    ):
        super().__init__(
            component_str=agent_generator_str,
            error_message=error_message,
            detail=detail,
        )


class AgentGeneratorBuildStepRuntimeError(
    ComponentRuntimeError,
    AgentGeneratorOperationError,
):
    """Raised when an agent generator build step encounters an unhandled error at runtime
    during agent generator operation.
    """

    code = "AGENT_GENERATOR_BUILD_STEP_RUNTIME_ERROR"
    _COMPONENT_TYPE = "agent generator build step"

    def __init__(
        self,
        agent_generator_build_step_str: str,
        error_message: str,
        detail: dict[str, JsonValue],
    ):
        super().__init__(
            component_str=agent_generator_build_step_str,
            error_message=error_message,
            detail=detail,
        )


class AgentGeneratorStopError(ComponentStopError, AgentGeneratorOperationError):
    """Raised when an agent generator fails to stop during agent generator operation."""

    code = "AGENT_GENERATOR_STOP_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        error_message: str,
        detail: dict[str, JsonValue],
    ):
        super().__init__(
            component_str=agent_generator_str,
            error_message=error_message,
            detail=detail,
        )


class AgentGeneratorStateError(
    ComponentStateError,
    AgentGeneratorsFrameworkError,
):
    """Base exception for all errors that occur due to invalid status transitions or
    operations performed on an agent generator in an invalid status.
    """

    code = "AGENT_GENERATOR_STATE_ERROR"


class AgentGeneratorNotRunningError(ComponentNotRunningError, AgentGeneratorStateError):
    """Raised when an operation is attempted on an agent generator that requires the agent
    generator to already be running but the agent generator is not running.
    """

    code = "AGENT_GENERATOR_NOT_RUNNING_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
    ):
        super().__init__(component_str=agent_generator_str)


class AgentGeneratorAlreadyRunningError(
    ComponentAlreadyRunningError,
    AgentGeneratorStateError,
):
    """Raised when an operation is attempted on an agent generator that requires the agent
    generator to not already be started or running but the agent generator is already
    started or running.
    """

    code = "AGENT_GENERATOR_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
    ):
        super().__init__(component_str=agent_generator_str)
