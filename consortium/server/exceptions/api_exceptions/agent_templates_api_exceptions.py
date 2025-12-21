from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class AgentTemplateNotFoundError(NotFoundError): ...


class AgentTemplateOptionNotFoundError(UnprocessableEntityError): ...


class AgentTemplateOptionValueValidationError(UnprocessableEntityError): ...


class MissingRequiredAgentTemplateOptionError(UnprocessableEntityError): ...
