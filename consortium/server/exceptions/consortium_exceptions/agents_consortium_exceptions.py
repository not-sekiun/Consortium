"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`AgentServiceError`][consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions.AgentServiceError]
        - [`AgentNotFoundError`][consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions.AgentNotFoundError]
"""

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class AgentServiceError(BaseConsortiumError):
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
