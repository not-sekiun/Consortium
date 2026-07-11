"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`AgentServiceError`][consortium.server.exceptions.service_exceptions.agents_service_exceptions.AgentServiceError]
        - [`AgentNotFoundError`][consortium.server.exceptions.service_exceptions.agents_service_exceptions.AgentNotFoundError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class AgentServiceError(BaseServiceError):
    """Base exception for all errors that occur within the agents service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "AGENT_SERVICE_ERROR"


class AgentNotFoundError(AgentServiceError):
    """Raised when the requested agent was not found in the agents service."""

    code = "AGENT_NOT_FOUND_ERROR"

    def __init__(self, agent_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent. No agent was found with the "
                f"provided agent ID '{agent_id}'."
            ),
        )
