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


class AgentNotFoundError(NotFoundError): ...


class AgentTaskNotFoundError(NotFoundError): ...


class AgentResultNotFoundError(NotFoundError): ...


class AgentCapabilityOptionValueValidationError(UnprocessableEntityError): ...


class MissingRequiredAgentCapabilityOptionError(UnprocessableEntityError): ...


class AgentCapabilityOptionNotFoundError(NotFoundError): ...
