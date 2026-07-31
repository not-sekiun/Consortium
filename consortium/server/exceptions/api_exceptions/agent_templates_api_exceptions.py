from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


# At the services level, Agent templates distinguish between not being found by their
# `agent_template_id` (`AGENT_TEMPLATE_ID_NOT_FOUND_ERROR`) or `label`
# (`AGENT_TEMPLATE_ID_NOT_FOUND_ERROR`). But this distinction does not exist at the API
# level hence we override using those error codes with this error code
class AgentTemplateNotFoundError(NotFoundError):
    code = "AGENT_TEMPLATE_NOT_FOUND_ERROR"


class AgentTemplateOptionNotFoundError(UnprocessableEntityError): ...


class AgentTemplateOptionValueValidationError(UnprocessableEntityError): ...


class MissingRequiredAgentTemplateOptionError(UnprocessableEntityError): ...


class AgentTemplateValidatingFunctionError(UnprocessableEntityError): ...
