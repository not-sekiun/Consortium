"""
Errors for /api/agent-templates endpoint.

HTTPError:
  NotFoundError:
    - AgentTemplateNotFoundError: Raised when the requested agent template is not found.
  UnprocessableEntityError:
    - AgentTemplateOptionNotFoundError: Raised when the provided agent template option
     is not found.
    - AgentTemplateOptionValueError: Raised when the provided agent template option's
     value is invalid.
"""

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class AgentTemplateNotFoundError(NotFoundError): ...


class AgentTemplateOptionNotFoundError(UnprocessableEntityError): ...


class AgentTemplateOptionValueValidationError(UnprocessableEntityError): ...


class MissingRequiredAgentTemplateOptionError(UnprocessableEntityError): ...
