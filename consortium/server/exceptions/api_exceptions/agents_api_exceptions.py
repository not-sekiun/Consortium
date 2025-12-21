from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class AgentNotFoundError(NotFoundError): ...


class AgentTaskNotFoundError(NotFoundError): ...


class AgentResultNotFoundError(NotFoundError): ...


class AgentCapabilityOptionValueValidationError(UnprocessableEntityError): ...


class MissingRequiredAgentCapabilityOptionError(UnprocessableEntityError): ...


class AgentCapabilityOptionNotFoundError(UnprocessableEntityError): ...


class AgentCapabilityNotFoundError(UnprocessableEntityError): ...
