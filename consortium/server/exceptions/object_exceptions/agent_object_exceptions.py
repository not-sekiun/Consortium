from typing import Any

from pydantic.config import JsonValue

from consortium.server.exceptions.object_exceptions.base_object_exception import (
    BaseObjectError,
)


class AgentsObjectError(BaseObjectError):
    """Base exception for all errors raised by agent objects.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "AGENTS_OBJECT_ERROR"


class AgentTaskNotFoundError(AgentsObjectError):
    """Raised when the requested task for a particular agent was not found."""

    code = "AGENT_TASK_NOT_FOUND_ERROR"

    def __init__(self, task_id: str):
        super().__init__(
            f"Failed to find the requested agent task. No agent task was found with "
            f"the provided task ID '{task_id}'.",
        )


class AgentTaskingError(AgentsObjectError):
    """Base exception for errors raised while tasking an agent."""

    code = "AGENT_TASKING_ERROR"


class AgentCapabilityNotFoundError(AgentTaskingError):
    """Raised when the agent tasking references a command that does not match any
    capability of the agent's type.
    """

    code = "AGENT_CAPABILITY_NOT_FOUND_ERROR"

    def __init__(self, command: str, agent_str: str, agent_type_str: str):
        super().__init__(
            message=(
                f"Failed to task the agent {agent_str} with the capability "
                f"'{command}'. The agent tasking provided contained a command that did "
                f"not correspond with any agent capabilities in that agent's type "
                f"'{agent_type_str}'."
            ),
        )


class AgentCapabilityOptionNotFoundError(AgentTaskingError):
    """Raised when the agent tasking references an option that does not match any option
    of the agent capability.
    """

    code = "AGENT_CAPABILITY_OPTION_NOT_FOUND_ERROR"

    def __init__(
        self,
        command: str,
        option_name: str,
        agent_str: str,
        agent_type_str: str,
    ):
        super().__init__(
            message=(
                f"Failed to task the agent {agent_str} with the capability "
                f"'{command}'. The agent tasking provided contained an argument "
                f"'{option_name}' that did not correspond with any options in that "
                f"agent capability for that agent's type '{agent_type_str}'."
            ),
        )


class AgentCapabilityValidatingFunctionError(AgentTaskingError):
    """Raised when an agent capability rejects its resolved arguments."""

    code = "AGENT_CAPABILITY_VALIDATING_FUNCTION_ERROR"

    def __init__(
        self,
        agent_str: str,
        command: str,
        error_message: str,
        detail: dict[str, JsonValue] | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to task the agent {agent_str} with the capability "
                f"'{command}'. The capabilities validating function "
                f"failed to validate its options. {error_message}"
            ),
            detail=detail,
        )


class MissingRequiredAgentCapabilityOptionError(AgentTaskingError):
    """Raised when a required option for an agent capability was not provided in the agent
    tasking.
    """

    code = "MISSING_REQUIRED_AGENT_CAPABILITY_OPTION_ERROR"

    def __init__(self, agent_str: str, agent_capability_name: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to task the agent '{agent_str}' with the agent capability "
                f"'{agent_capability_name}'. The required option '{option_name}' was "
                f"not provided."
            ),
        )


class AgentCapabilityOptionValueValidationError(AgentTaskingError):
    """Raised when the provided value for an agent capability option fails validation
    during agent tasking.
    """

    code = "AGENT_CAPABILITY_OPTION_VALUE_VALIDATION_ERROR"

    def __init__(
        self,
        agent_str: str,
        option_name: str,
        option_value: Any,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to task the agent {agent_str}. The provided value "
                f"'{option_value}' for the option '{option_name}' is invalid. "
                f"{error_message}"
            ),
        )


class AgentCreationError(AgentsObjectError):
    """Base exception for errors raised while creating an agent."""

    code = "AGENT_CREATION_ERROR"


class AgentCreationParameterTypeError(AgentCreationError):
    """Raised when a parameter provided during agent creation is not of the expected
    type.
    """

    code = "AGENT_CREATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to create the agent. The parameter "
                f"'{parameter_name}' must be of type '{parameter_type}' in the "
                f"agent's provided parameters."
            ),
        )


class AgentTypeResolutionError(AgentCreationError):
    """Raised when the agent's type could not be resolved during agent creation."""

    code = "AGENT_TYPE_RESOLUTION_ERROR"

    @classmethod
    def _due_to_payload_not_found_error(cls, payload_id):
        return cls(
            message=(
                f"Failed to create the agent. Could not resolve the agent type "
                f"from a known framework payload because no payload with the provided "
                f"payload ID '{payload_id}' was found."
            ),
            detail={
                "payload_id": payload_id,
            },
        )

    @classmethod
    def _due_to_agent_type_not_found_error(cls, agent_type_name: str):
        return cls(
            message=(
                f"Failed to create the agent. Could not resolve the agent type "
                f"because no agent type with the name '{agent_type_name}' was found."
            ),
            detail={
                "agent_type_name": agent_type_name,
            },
        )

    @classmethod
    def _due_to_no_identifier_provided(cls):
        return cls(
            message=(
                "Failed to create the agent. Could not resolve the agent type "
                "because no identifier (payload ID or agent type name) was provided."
            ),
        )
