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

from typing import Any

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class AgentTemplateNotFoundError(NotFoundError):
    code = "AGENT_TEMPLATE_NOT_FOUND_ERROR"


class AgentTemplateOptionNotFoundError(UnprocessableEntityError):
    code = "AGENT_TEMPLATE_OPTION_NOT_FOUND_ERROR"


class AgentTemplateOptionValueError(UnprocessableEntityError):
    code = "AGENT_TEMPLATE_OPTION_VALUE_ERROR"
