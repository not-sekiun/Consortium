"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`AgentGeneratorsServiceError`][consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions.AgentGeneratorsServiceError]
        - [`AgentGeneratorNotFoundError`][consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions.AgentGeneratorNotFoundError]
        - [`AgentGeneratorAlreadyExistsError`][consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions.AgentGeneratorAlreadyExistsError]
        - [`AgentGeneratorParameterUpdateError`][consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions.AgentGeneratorParameterUpdateError]
            - [`InvalidAgentGeneratorParameterNameError`][consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions.InvalidAgentGeneratorParameterNameError]
            - [`InvalidAgentGeneratorParameterValueError`][consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions.InvalidAgentGeneratorParameterValueError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class AgentGeneratorsServiceError(BaseServiceError):
    """Base exception for all errors that occur within the agent generators service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "AGENT_GENERATORS_SERVICE_ERROR"


class AgentGeneratorNotFoundError(AgentGeneratorsServiceError):
    """Raised when the requested agent generator was not found in the agent generators
    service.
    """

    code = "AGENT_GENERATOR_NOT_FOUND_ERROR"

    def __init__(self, agent_generator_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent generator. No agent generator was "
                f"found with the provided agent generator ID '{agent_generator_id}'."
            ),
        )


class AgentGeneratorAlreadyExistsError(AgentGeneratorsServiceError):
    """Raised when an agent generator with the provided agent generator ID already exists
    in the agent generators service.
    """

    code = "AGENT_GENERATOR_ALREADY_EXISTS_ERROR"

    def __init__(self, agent_generator_id: str):
        super().__init__(
            message=(
                f"Failed to add the specified agent generator. An agent generator "
                f"already exists with the agent generator ID '{agent_generator_id}'."
            ),
        )


class AgentGeneratorParameterUpdateError(AgentGeneratorsServiceError):
    """Base exception for agent generator parameter update errors."""

    code = "AGENT_GENERATOR_PARAMETER_UPDATE_ERROR"


class InvalidAgentGeneratorParameterNameError(AgentGeneratorParameterUpdateError):
    """Raised when the provided parameter name was not found on the agent generator during
    a parameter update.
    """

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
    """Raised when the provided value for an agent generator parameter is invalid during a
    parameter update.
    """

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
