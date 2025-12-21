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
