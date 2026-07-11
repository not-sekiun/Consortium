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
    code = "AGENT_SERVICE_ERROR"


class AgentNotFoundError(AgentServiceError):
    code = "AGENT_NOT_FOUND_ERROR"

    def __init__(self, agent_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent. No agent was found with the "
                f"provided agent ID '{agent_id}'."
            ),
        )
