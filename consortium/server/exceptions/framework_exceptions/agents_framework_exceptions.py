from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class AgentsFrameworkError(BaseFrameworkException):
    pass


class AgentTaskNotFoundError(AgentsFrameworkError):
    def __init__(self, task_id: str):
        super().__init__(
            f"Failed to find the requested agent task. No agent task was found with "
            f"the provided task ID '{task_id}'.",
        )


class AgentResultNotFoundError(AgentsFrameworkError):
    pass


class AgentResultIDNotFoundError(AgentResultNotFoundError):
    def __init__(self, result_id: str):
        super().__init__(
            f"Failed to find the requested agent result. No agent result was found "
            f"with the provided result ID '{result_id}'.",
        )


class AgentResultTaskIDNotFoundError(AgentResultNotFoundError):
    def __init__(self, task_id: str):
        super().__init__(
            f"Failed to find the requested agent result. No agent result was found "
            f"that corresponded with the agent task with the provided task ID "
            f"'{task_id}'.",
        )


class AgentResultHasNoCorrespondingTaskError(AgentsFrameworkError):
    def __init__(self, result_id: str, corresponding_task_id: str, agent_str: str):
        super().__init__(
            message=(
                f"Failed to add the agent result '{result_id}' to the agent "
                f"{agent_str}. The agent result that was added corresponds to task ID "
                f"'{corresponding_task_id}', but no running task exists with that ID."
            ),
        )


class AgentCapabilityNotFoundError(AgentsFrameworkError):
    def __init__(self, command: str, agent_str: str, agent_type_str: str):
        super().__init__(
            message=(
                f"Failed to task the agent {agent_str} with the capability "
                f"'{command}'. The agent tasking provided contained a command that did "
                f"not correspond with any agent capabilities in that agent's type "
                f"'{agent_type_str}'."
            ),
        )


class AgentCapabilityArgumentNotFoundError(AgentsFrameworkError):
    def __init__(
        self,
        command: str,
        argument: str,
        agent_str: str,
        agent_type_str: str,
    ):
        super().__init__(
            message=(
                f"Failed to task the agent {agent_str} with the capability "
                f"'{command}'. The agent tasking provided contained an argument "
                f"'{argument}' that did not correspond with any arguments in that "
                f"agent capability for that agent's type '{agent_type_str}'."
            ),
        )
