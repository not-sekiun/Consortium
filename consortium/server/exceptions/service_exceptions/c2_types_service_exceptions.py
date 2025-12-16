"""
Exception hierarchy for the c2 types service.

- [BaseServiceException][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceException]
    - [C2TypesServiceError][consortium.server.exceptions.service_exceptions.c2_types_service_exceptions.C2TypesServiceError]
        - [ListenerTypeNotFoundError][consortium.server.exceptions.service_exceptions.c2_types_service_exceptions.ListenerTypeNotFoundError]
        - [AgentTypeNotFoundError][consortium.server.exceptions.service_exceptions.c2_types_service_exceptions.AgentTypeNotFoundError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class C2TypesServiceError(BaseServiceException):
    """
    Base exception for all C2 types service related errors.
    """

    code = "C2_TYPES_SERVICE_ERROR"


class ListenerTypeNotFoundError(C2TypesServiceError):
    """
    Raised when a requested listener type cannot be found by its listener type name.

    Args:
        listener_type_name (str): The name of the listener type that was not found.
    """

    code = "LISTENER_TYPE_NOT_FOUND_ERROR"

    def __init__(self, listener_type_name: str):
        super().__init__(
            message=(
                f"Failed to find the requested listener type. No listener type "
                f"could be found with the provided listener type name "
                f"'{listener_type_name}'."
            ),
        )


class AgentTypeNotFoundError(C2TypesServiceError):
    """
    Raised when a requested agent type cannot be found by its agent type name.

    Args:
        agent_type_name (str): The name of the agent type that was not found.
    """

    code = "AGENT_TYPE_NOT_FOUND_ERROR"

    def __init__(self, agent_type_name: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent type. No agent type could be "
                f"found with the provided agent type name '{agent_type_name}'."
            ),
        )
