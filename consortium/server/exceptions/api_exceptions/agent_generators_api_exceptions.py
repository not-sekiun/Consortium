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

from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ConflictError,
    InternalServerError,
    NotFoundError,
    UnprocessableEntityError,
)


class AgentGeneratorNotFoundError(NotFoundError): ...


class AgentTemplateResolutionError(InternalServerError):
    code = "AGENT_TEMPLATE_RESOLUTION_ERROR"

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


class InvalidAgentGeneratorParameterNameError(UnprocessableEntityError): ...


class InvalidAgentGeneratorParameterValueError(UnprocessableEntityError): ...


class AgentGeneratorAlreadyRunningError(ConflictError): ...


class AgentGeneratorNotRunningError(ConflictError): ...


class AgentGeneratorStartError(ConflictError): ...


class AgentGeneratorStopError(ConflictError): ...
