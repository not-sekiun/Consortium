from typing import Any

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class AgentsError(BaseConsortiumError):
    code = "AGENTS_ERROR"


class AgentsFrameworkError(AgentsError):
    code = "AGENTS_FRAMEWORK_ERROR"


class AgentTaskNotFoundError(AgentsFrameworkError):
    code = "AGENT_TASK_NOT_FOUND_ERROR"

    def __init__(self, task_id: str):
        super().__init__(
            f"Failed to find the requested agent task. No agent task was found with "
            f"the provided task ID '{task_id}'.",
        )


class AgentResultNotFoundError(AgentsFrameworkError):
    code = "AGENT_RESULT_NOT_FOUND_ERROR"


class AgentResultIDNotFoundError(AgentResultNotFoundError):
    code = "AGENT_RESULT_ID_NOT_FOUND_ERROR"

    def __init__(self, result_id: str):
        super().__init__(
            f"Failed to find the requested agent result. No agent result was found "
            f"with the provided result ID '{result_id}'.",
        )


class AgentResultTaskIDNotFoundError(AgentResultNotFoundError):
    code = "AGENT_RESULT_TASK_ID_NOT_FOUND_ERROR"

    def __init__(self, task_id: str):
        super().__init__(
            f"Failed to find the requested agent result. No agent result was found "
            f"that corresponded with the agent task with the provided task ID "
            f"'{task_id}'.",
        )


class AgentResultHasNoCorrespondingTaskError(AgentsFrameworkError):
    code = "AGENT_RESULT_HAS_NO_CORRESPONDING_TASK_ERROR"

    def __init__(self, result_id: str, corresponding_task_id: str, agent_str: str):
        super().__init__(
            message=(
                f"Failed to add the agent result '{result_id}' to the agent "
                f"{agent_str}. The agent result that was added corresponds to task ID "
                f"'{corresponding_task_id}', but no running task exists with that ID."
            ),
        )


class AgentTaskingError(AgentsFrameworkError):
    code = "AGENT_CAPABILITY_OPTION_ERROR"


class AgentCapabilityNotFoundError(AgentTaskingError):
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


class MissingRequiredAgentCapabilityOptionError(AgentTaskingError):
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
                f"Failed to task the agent '{agent_str}'. The provided value "
                f"'{option_value}' for the option '{option_name}' is invalid. "
                f"{error_message}"
            ),
        )


class AgentCreationError(AgentsFrameworkError):
    code = "AGENT_CREATION_ERROR"


class AgentCreationParameterTypeError(AgentCreationError):
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


class AgentServiceError(AgentsError):
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
