"""
Exception hierarchy for the c2 types service:

- BaseServiceException: Base class for all service-related exceptions.
  - C2TypesServiceError: Base exception for all C2TypesService related errors.
    - ListenerTypeNotFoundError: Raised when a requested listener type cannot be found
    by its listener type ID.
    - AgentTypeNotFoundError: Raised when a requested agent type cannot be found by its
    agent type ID.
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class C2TypesServiceError(BaseServiceException):
    code = "C2_TYPES_SERVICE_ERROR"


class ListenerTypeNotFoundError(C2TypesServiceError):
    code = "LISTENER_TYPE_NOT_FOUND_ERROR"

    def __init__(self, listener_type_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested listener type. No listener type "
                f"could be found with the provided listener type ID "
                f"'{listener_type_id}'."
            ),
        )


class AgentTypeNotFoundError(C2TypesServiceError):
    code = "AGENT_TYPE_NOT_FOUND_ERROR"

    def __init__(self, agent_type_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent type. No agent type could be "
                f"found with the requested agent type ID '{agent_type_id}'."
            ),
        )
