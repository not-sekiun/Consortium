from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)


class AgentGeneratorNotFoundError(NotFoundError): ...


class InvalidAgentGeneratorParameterNameError(UnprocessableEntityError): ...


class InvalidAgentGeneratorParameterValueError(UnprocessableEntityError): ...


class AgentGeneratorAlreadyRunningError(ConflictError): ...


class AgentGeneratorNotRunningError(ConflictError): ...


class AgentGeneratorStartError(ConflictError): ...


class AgentGeneratorStopError(ConflictError): ...
