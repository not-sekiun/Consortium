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
    pass


class AgentGeneratorNotFoundError(AgentGeneratorsServiceError):
    def __init__(self, agent_generator_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent generator. No agent generator was "
                f"found with the provided agent generator ID '{agent_generator_id}'."
            ),
        )


class AgentGeneratorAlreadyExistsError(AgentGeneratorsServiceError):
    def __init__(self, agent_generator_id: str):
        super().__init__(
            message=(
                f"Failed to add the specified agent generator. An agent generator "
                f"already exists with the agent generator ID '{agent_generator_id}'."
            ),
        )


class AgentGeneratorOperationError(AgentGeneratorsServiceError):
    def __init__(self, message: str = "", detail: Any = None):
        self.detail = detail
        super().__init__(message=message)


class AgentGeneratorStartError(AgentGeneratorOperationError):
    pass


class AgentGeneratorStopError(AgentGeneratorOperationError):
    pass


class AgentGeneratorStateError(AgentGeneratorsServiceError):
    pass


class AgentGeneratorAlreadyRunningError(AgentGeneratorStateError):
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
    pass


class InvalidAgentGeneratorParameterNameError(AgentGeneratorParameterUpdateError):
    def __init__(self, agent_generator_str: str, parameter_name: str):
        super().__init__(
            message=(
                f"Failed to update agent generator parameter for agent generator "
                f"'{agent_generator_str}'. The provided parameter name '{parameter_name}' "
                f"is not a valid parameter name."
            ),
        )


class InvalidAgentGeneratorParameterValueError(AgentGeneratorParameterUpdateError):
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
    def __init__(self, message: str = "", detail: Any = None):
        self.detail = detail
        super().__init__(message=message)


# This is a wrapper exception for AgentTemplateOptionNotFoundError from the
# agent templates framework exceptions. It just needs to pass on the message and detail
# data from that exception.
class AgentTemplateOptionNotFoundError(AgentGeneratorCreationError):
    pass


# This is a wrapper exception for AgentTemplateOptionValueError from the agent
# templates framework exceptions. It just needs to pass on the message and detail data
# from that exception.
class AgentTemplateOptionValueError(AgentGeneratorCreationError):
    pass
