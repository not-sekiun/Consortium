"""
- BaseServiceException: Base class for all exceptions raised by the agent generators
service.
  - AgentGeneratorsServiceError: Base class for all exceptions raised by the agent
  generators service.
    - AgentGeneratorNotFoundError: Agent generator not found.
    - AgentGeneratorAlreadyExistsError: Agent generator already exists.
    - AgentGeneratorParameterUpdateError:
      - InvalidAgentGeneratorParameterNameError:
      - InvalidAgentGeneratorParameterValueError:
"""

from typing import Any

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class AgentGeneratorsServiceError(BaseServiceException):
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


class AgentGeneratorOperationError(AgentGeneratorsServiceError):
    code = "AGENT_GENERATOR_OPERATION_ERROR"

    def __init__(self, message: str = "", detail: Any = None):
        super().__init__(message=message, detail=detail)


class AgentGeneratorStartError(AgentGeneratorOperationError):
    code = "AGENT_GENERATOR_START_ERROR"


class AgentGeneratorStopError(AgentGeneratorOperationError):
    code = "AGENT_GENERATOR_STOP_ERROR"


class AgentGeneratorStateError(AgentGeneratorsServiceError):
    code = "AGENT_GENERATOR_STATE_ERROR"


class AgentGeneratorAlreadyRunningError(AgentGeneratorStateError):
    code = "AGENT_GENERATOR_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the agent generator. The "
            "agent generator is already running which conflicts with the operation "
            "that was requested."
        ),
    ):
        super().__init__(message=message)


class AgentGeneratorNotRunningError(AgentGeneratorStateError):
    code = "AGENT_GENERATOR_NOT_RUNNING_ERROR"

    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the agent generator. The "
            "agent generator is not running which conflicts with the operation that "
            "was requested."
        ),
    ):
        super().__init__(message=message)


class AgentGeneratorParameterUpdateError(AgentGeneratorsServiceError):
    code = "AGENT_GENERATOR_PARAMETER_UPDATE_ERROR"


class InvalidAgentGeneratorParameterNameError(AgentGeneratorParameterUpdateError):
    code = "INVALID_AGENT_GENERATOR_PARAMETER_NAME_ERROR"

    def __init__(self, agent_generator_str: str, parameter_name: str):
        super().__init__(
            message=(
                f"Failed to update agent generator parameter for agent generator "
                f"'{agent_generator_str}'. The provided parameter name '{parameter_name}' "
                f"is not a valid parameter name."
            ),
        )


class InvalidAgentGeneratorParameterValueError(AgentGeneratorParameterUpdateError):
    code = "INVALID_AGENT_GENERATOR_PARAMETER_VALUE_ERROR"

    def __init__(
        self,
        agent_generator_str: str,
        parameter_name: str,
        parameter_value: str,
        validation_error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to update the agent generator parameter for agent generator "
                f"'{agent_generator_str}'. The provided parameter value "
                f"'{parameter_value}' failed validation for the parameter "
                f"'{parameter_name}': {validation_error_message}"
            ),
        )


class AgentGeneratorCreationError(AgentGeneratorsServiceError):
    code = "AGENT_GENERATOR_CREATION_ERROR"

    def __init__(self, message: str = "", detail: Any = None):
        super().__init__(message=message, detail=detail)


# This is a wrapper exception for AgentTemplateOptionNotFoundError from the
# agent templates framework exceptions. It just needs to pass on the message and detail
# data from that exception.
class AgentTemplateOptionNotFoundError(AgentGeneratorCreationError):
    code = "AGENT_TEMPLATE_OPTION_NOT_FOUND_ERROR"


# This is a wrapper exception for AgentTemplateOptionValueError from the agent
# templates framework exceptions. It just needs to pass on the message and detail data
# from that exception.
class AgentTemplateOptionValueError(AgentGeneratorCreationError):
    code = "AGENT_TEMPLATE_OPTION_VALUE_ERROR"
