from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class AgentServiceError(BaseServiceException):
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


# class AgentTaskNotFoundError(AgentServiceError):
#     code = "AGENT_TASK_NOT_FOUND_ERROR"
#
#     def __init__(self, task_id: str):
#         super().__init__(
#             message=(
#                 f"Failed to find the requested agent task. No agent task was found with the "
#                 f"provided agent task ID '{task_id}'."
#             ),
#         )
#
#
# class AgentResultNotFoundError(AgentServiceError):
#     code = "AGENT_RESULT_NOT_FOUND_ERROR"
#
#     def __init__(self, result_id: str):
#         super().__init__(
#             message=(
#                 f"Failed to find the requested agent result. No agent result was found "
#                 f"with the provided agent result ID '{result_id}'."
#             ),
#         )
#
#
# class AgentTaskingError(AgentServiceError):
#     code = "AGENT_TASKING_ERROR"
#
#
# class AgentCapabilityOptionValueValidationError(AgentTaskingError):
#     code = "AGENT_CAPABILITY_OPTION_VALUE_VALIDATION_ERROR"
#
#
# class MissingRequiredAgentCapabilityOptionError(AgentTaskingError):
#     code = "MISSING_REQUIRED_AGENT_CAPABILITY_OPTION_ERROR"
#
#
# class AgentCapabilityOptionNotFoundError(AgentTaskingError):
#     code = "AGENT_CAPABILITY_OPTION_NOT_FOUND_ERROR"
#
#
# class AgentCapabilityNotFoundError(AgentTaskingError):
#     code = "AGENT_CAPABILITY_NOT_FOUND_ERROR"
