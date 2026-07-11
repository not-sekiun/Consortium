"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`C2TypesServiceError`][consortium.server.exceptions.service_exceptions.c2_types_service_exceptions.C2TypesServiceError]
        - [`ListenerTypeNotFoundError`][consortium.server.exceptions.service_exceptions.c2_types_service_exceptions.ListenerTypeNotFoundError]
        - [`AgentTypeNotFoundError`][consortium.server.exceptions.service_exceptions.c2_types_service_exceptions.AgentTypeNotFoundError]
        - [`DuplicateAgentTypeNameError`][consortium.server.exceptions.service_exceptions.c2_types_service_exceptions.DuplicateAgentTypeNameError]
        - [`UnresolvableAgentTypeReferenceError`][consortium.server.exceptions.service_exceptions.c2_types_service_exceptions.UnresolvableAgentTypeReferenceError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class C2TypesServiceError(BaseServiceError):
    """Base exception for all errors that occur within the C2 types service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "C2_TYPES_SERVICE_ERROR"


class ListenerTypeNotFoundError(C2TypesServiceError):
    """Raised when the requested listener type was not found in the C2 types service."""

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
    """Raised when the requested agent type was not found in the C2 types service."""

    code = "AGENT_TYPE_NOT_FOUND_ERROR"

    def __init__(self, agent_type_name: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent type. No agent type could be "
                f"found with the provided agent type name '{agent_type_name}'."
            ),
        )


class DuplicateAgentTypeNameError(C2TypesServiceError):
    """Raised when multiple distinct agent types with the same name are found in the C2
    types service.
    """

    code = "DUPLICATE_AGENT_TYPE_NAME_ERROR"

    def __init__(
        self,
        agent_template_str: str,
        conflicting_agent_template_str: str,
        agent_type_name: str,
    ):
        super().__init__(
            message=(
                f"Failed to resolve agent type references. Agent template "
                f"{agent_template_str} declared agent type '{agent_type_name}', but "
                f"{conflicting_agent_template_str} already declared another distinct"
                f"agent type with that name. Check that distinct agent types declare "
                f"distinct names."
            ),
        )


class UnresolvableAgentTypeReferenceError(C2TypesServiceError):
    """Raised when an agent type reference cannot be resolved to a known agent type in
    the C2 types service.
    """

    code = "UNRESOLVABLE_AGENT_TYPE_REFERENCE_ERROR"

    def __init__(self, agent_template_str: str, agent_type_name: str):
        super().__init__(
            message=(
                f"Failed to resolve agent type reference for agent template "
                f"{agent_template_str}. No known agent type with the name "
                f"'{agent_type_name}' could be found. Check that at least one agent "
                f"type was defined with that name and loaded for the reference to be "
                f"resolved."
            ),
        )
