"""Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`C2TypesError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.C2TypesError]
        - [`C2TypesFrameworkError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.C2TypesFrameworkError]
            - [`ListenerTypeConfigurationError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.ListenerTypeConfigurationError]
                - [`ListenerTypeConfigurationParameterTypeError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.ListenerTypeConfigurationParameterTypeError]
                - [`EmptyListenerTypeNameError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.EmptyListenerTypeNameError]
            - [`AgentTypeConfigurationError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.AgentTypeConfigurationError]
                - [`AgentTypeConfigurationParameterTypeError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.AgentTypeConfigurationParameterTypeError]
                - [`EmptyAgentTypeNameError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.EmptyAgentTypeNameError]
        - [`C2TypesServiceError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.C2TypesServiceError]
            - [`ListenerTypeNotFoundError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.ListenerTypeNotFoundError]
            - [`AgentTypeNotFoundError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.AgentTypeNotFoundError]
            - [`DuplicateAgentTypeNameError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.DuplicateAgentTypeNameError]
            - [`UnresolvableAgentTypeReferenceError`][consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions.UnresolvableAgentTypeReferenceError]
"""

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class C2TypesError(BaseConsortiumError):
    """Base exception for all C2 types-related errors."""

    code = "C2_TYPES_ERROR"


class C2TypesFrameworkError(C2TypesError):
    """Base exception for all errors that occur within the C2 types framework."""

    code = "C2_TYPES_FRAMEWORK_ERROR"


class ListenerTypeConfigurationError(C2TypesFrameworkError):
    """Base exception for all errors that occur when a listener type fails to be configured."""

    code = "LISTENER_TYPE_CONFIGURATION_ERROR"


class ListenerTypeConfigurationParameterTypeError(ListenerTypeConfigurationError):
    """Raised when a provided listener type parameter is not of the expected type during
    listener type configuration.
    """

    code = "LISTENER_TYPE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        listener_type_filepath: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to configure the listener type defined at "
                f"'{listener_type_filepath}'. The parameter '{parameter_name}' "
                f"must be of type '{parameter_type}' in the listener type's "
                f"definition."
            ),
        )


class EmptyListenerTypeNameError(ListenerTypeConfigurationError):
    """Raised when an empty name is provided for a listener type during configuration."""

    code = "EMPTY_LISTENER_TYPE_NAME_ERROR"

    def __init__(self, listener_type_filepath: str):
        super().__init__(
            f"Failed to configure the listener type defined at "
            f"'{listener_type_filepath}'. The name provided in the listener type's "
            f"definition during configuration cannot be empty.",
        )


class AgentTypeConfigurationError(C2TypesFrameworkError):
    """Base exception for all errors that occur when an agent type fails to be configured."""

    code = "AGENT_TYPE_CONFIGURATION_ERROR"


class AgentTypeConfigurationParameterTypeError(AgentTypeConfigurationError):
    """Raised when a provided agent type parameter is not of the expected type during
    agent type configuration.
    """

    code = "AGENT_TYPE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        agent_type_filepath: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to configure the agent type defined at "
                f"'{agent_type_filepath}'. The parameter '{parameter_name}' "
                f"must be of type '{parameter_type}' in the agent type's "
                f"definition."
            ),
        )


class EmptyAgentTypeNameError(AgentTypeConfigurationError):
    """Raised when an empty name is provided for an agent type during configuration."""

    code = "EMPTY_AGENT_TYPE_NAME_ERROR"

    def __init__(self, agent_type_filepath: str):
        super().__init__(
            f"Failed to configure the agent type defined at "
            f"'{agent_type_filepath}'. The name provided in the agent type's "
            f"definition during configuration cannot be empty.",
        )


class C2TypesServiceError(C2TypesError):
    """Base exception for all errors that occur within the C2 types service."""

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
