"""
Errors for the endpoint /api/agent-generators.

- HTTPError
  - NotFoundError
    - AgentGeneratorNotFoundError: Raised when the requested agent generator is not found.
  - UnprocessableEntityError
    - AgentGeneratorParameterUpdateError
      - InvalidAgentGeneratorParameterNameError: Raised when an invalid parameter name
      is provided for an agent generator.
      - InvalidAgentGeneratorParameterValueError: Raised when an invalid parameter
      value is provided for an agent generator.
  - InternalServerError
    - AgentTemplateResolutionError: Raised when there's an error resolving the agent
    template for a given agent type.
- AgentGeneratorError
 - AgentGeneratorStateError
   - AgentGeneratorAlreadyRunningError: Raised when attempting to start an agent
   generator that is already running.
   - AgentGeneratorNotRunningError: Raised when attempting to perform an operation on a
   non-running agent generator.
 - AgentGeneratorOperationError
   - AgentGeneratorStartError: Raised when there's an error starting an agent generator.
   - AgentGeneratorBuildError: Raised when there's an error building an agent generator.
   - AgentGeneratorStopError: Raised when there's an error stopping an agent generator.
   - AgentGeneratorCancellationError: Raised when there's an error cancelling an agent
   generator operation.
"""

from typing import Any

from consortium.framework.c2_types import BaseAgentType
from consortium.server.exceptions.api_exceptions.base_api_exception import (
    BaseAPIException,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ConflictError,
    InternalServerErrorError,
    NotFoundError,
    UnprocessableEntityError,
)


class AgentGeneratorNotFoundError(NotFoundError):
    code = "AGENT_GENERATOR_NOT_FOUND_ERROR"


class AgentTemplateResolutionError(InternalServerErrorError):
    code = ("AGENT_TEMPLATE_RESOLUTION_ERROR",)

    def __init__(
        self,
        agent_type: BaseAgentType,
    ) -> None:
        super().__init__(
            message=(
                "Failed to resolve the agent's agent template for the given agent type "
                f'with agent type ID "{agent_type.agent_type_id}".'
            ),
            detail={"agent_type": agent_type.to_json()},
        )


class InvalidAgentGeneratorParameterNameError(UnprocessableEntityError):
    code = "INVALID_LISTENER_PARAMETER_NAME_ERROR"


class InvalidAgentGeneratorParameterValueError(UnprocessableEntityError):
    code = "INVALID_AGENT_GENERATOR_PARAMETER_VALUE_ERROR"


class AgentGeneratorAlreadyRunningError(ConflictError):
    code = "AGENT_GENERATOR_ALREADY_RUNNING_ERROR"


class AgentGeneratorNotRunningError(ConflictError):
    code = "AGENT_GENERATOR_NOT_RUNNING_ERROR"


class AgentGeneratorStartError(BaseAPIException):
    # TODO: Consider making BaseAPIException's status code default to 400 to further
    #  cut code. No code: write nothing, deploy nowhere.
    status_code = 400
    code = "AGENT_GENERATOR_START_ERROR"


class AgentGeneratorStopError(BaseAPIException):
    status_code = 400
    code = "AGENT_GENERATOR_STOP_ERROR"
