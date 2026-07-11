"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`AgentGeneratorsServiceError`][consortium.server.exceptions.consortium_exceptions.agent_generators_consortium_exceptions.AgentGeneratorsServiceError]
        - [`AgentGeneratorNotFoundError`][consortium.server.exceptions.consortium_exceptions.agent_generators_consortium_exceptions.AgentGeneratorNotFoundError]
        - [`AgentGeneratorAlreadyExistsError`][consortium.server.exceptions.consortium_exceptions.agent_generators_consortium_exceptions.AgentGeneratorAlreadyExistsError]
        - [`AgentGeneratorParameterUpdateError`][consortium.server.exceptions.consortium_exceptions.agent_generators_consortium_exceptions.AgentGeneratorParameterUpdateError]
            - [`InvalidAgentGeneratorParameterNameError`][consortium.server.exceptions.consortium_exceptions.agent_generators_consortium_exceptions.InvalidAgentGeneratorParameterNameError]
            - [`InvalidAgentGeneratorParameterValueError`][consortium.server.exceptions.consortium_exceptions.agent_generators_consortium_exceptions.InvalidAgentGeneratorParameterValueError]
"""

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class AgentGeneratorsServiceError(BaseConsortiumError):
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
