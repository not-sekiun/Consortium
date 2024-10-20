"""
Errors for the api endpoint /api/listeners.
- HTTPError
  - NotFoundError
    - AgentNotFoundError: Raised when the requested agent is not found.
    - AgentTaskNotFoundError: Raised when the requested agent task is not found.
    - AgentResultNotFoundError: Raised when the requested agent result is not found.
"""

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class AgentNotFoundError(NotFoundError):
    code = "AGENT_NOT_FOUND_ERROR"


class AgentTaskNotFoundError(NotFoundError):
    code = "AGENT_TASK_NOT_FOUND_ERROR"


class AgentResultNotFoundError(NotFoundError):
    code = "AGENT_RESULT_NOT_FOUND_ERROR"


class AgentTaskingOptionValueValidationError(UnprocessableEntityError):
    code = "AGENT_TASKING_OPTION_VALUE_VALIDATION_ERROR"


class AgentTaskingRequiredOptionValueNotSetError(UnprocessableEntityError):
    code = "AGENT_TASKING_REQUIRED_OPTION_VALUE_NOT_SET_ERROR"
