from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class AgentsFrameworkError(BaseFrameworkException):
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


class AgentCapabilityNotFoundError(AgentsFrameworkError):
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


class AgentCapabilityOptionError(AgentsFrameworkError):
    code = "AGENT_CAPABILITY_OPTION_ERROR"


class AgentCapabilityOptionNotFoundError(AgentCapabilityOptionError):
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


class MissingRequiredAgentCapabilityOptionError(AgentCapabilityOptionError):
    code = "MISSING_REQUIRED_AGENT_CAPABILITY_OPTION_ERROR"

    def __init__(self, agent_str: str, agent_capability_name: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to task the agent '{agent_str}' with the agent capability "
                f"'{agent_capability_name}'. The required option '{option_name}' was "
                f"not provided."
            ),
        )


class AgentCapabilityOptionValueValidationError(AgentCapabilityOptionError):
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
