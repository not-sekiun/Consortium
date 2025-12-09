from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class AgentServiceError(BaseServiceException):
    code = "AGENT_SERVICE_ERROR"


class AgentNotFoundError(AgentServiceError):
    code = "AGENT_NOT_FOUND_ERROR"

    def __init__(self, agent_id: str):
        super().__init__(
            f"Failed to find the requested agent. No agent was found with the "
            f"provided agent ID '{agent_id}'.",
        )


class AgentTaskNotFoundError(AgentServiceError):
    code = "AGENT_TASK_NOT_FOUND_ERROR"

    def __init__(self, task_id: str):
        super().__init__(
            f"Failed to find the requested agent task. No agent task was found with the "
            f"provided agent task ID '{task_id}'.",
        )


class AgentResultNotFoundError(AgentServiceError):
    code = "AGENT_RESULT_NOT_FOUND_ERROR"

    def __init__(self, result_id: str):
        super().__init__(
            f"Failed to find the requested agent result. No agent result was found "
            f"with the provided agent result ID '{result_id}'.",
        )


class AgentTaskingError(AgentServiceError):
    code = "AGENT_TASKING_ERROR"


class AgentTaskingOptionValidationError(AgentTaskingError):
    code = "AGENT_TASKING_OPTION_VALIDATION_ERROR"

    def __init__(self, agent_str: str, error_message: str):
        super().__init__(
            f"Failed to task agent {agent_str}. {error_message}",
        )


class AgentTaskingRequiredOptionValueNotSetError(AgentTaskingError):
    code = "AGENT_TASKING_REQUIRED_OPTION_VALUE_NOT_SET_ERROR"

    def __init__(self, agent_str: str, error_message: str):
        super().__init__(
            f"Failed to task agent {agent_str}. {error_message}",
        )
