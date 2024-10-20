from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class AgentServiceError(BaseServiceException):
    pass


class AgentNotFoundError(AgentServiceError):
    def __init__(self, agent_id: str):
        super().__init__(
            f"Failed to find the requested agent. No agent was found with the "
            f"provided agent ID '{agent_id}'.",
        )


class AgentTaskNotFoundError(AgentServiceError):
    def __init__(self, task_id: str):
        super().__init__(
            f"Failed to find the requested agent task. No agent task was found with the "
            f"provided agent task ID '{task_id}'.",
        )


class AgentResultNotFoundError(AgentServiceError):
    def __init__(self, result_id: str):
        super().__init__(
            f"Failed to find the requested agent result. No agent result was found "
            f"with the provided agent result ID '{result_id}'.",
        )


class AgentTaskingError(AgentServiceError):
    pass


class AgentTaskingOptionValidationError(AgentTaskingError):
    def __init__(self, agent_str: str, error_message: str):
        super().__init__(
            f"Failed to task agent {agent_str}. {error_message}",
        )


class AgentTaskingRequiredOptionValueNotSetError(AgentTaskingError):
    def __init__(self, agent_str: str, error_message: str):
        super().__init__(
            f"Failed to task agent {agent_str}. {error_message}",
        )
