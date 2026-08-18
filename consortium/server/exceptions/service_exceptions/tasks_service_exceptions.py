from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)
from consortium.server.models.task_models import TaskState


class TasksServiceError(BaseServiceError):
    """Base exception for all errors that occur within the tasks service."""

    code = "TASKS_SERVICE_ERROR"


class TaskAgentMismatchError(TasksServiceError):
    """Raised when a task is registered against an agent that does not own it."""

    code = "TASK_AGENT_MISMATCH_ERROR"

    def __init__(self, task_agent_id: str, agent_id: str) -> None:
        super().__init__(
            message=(
                f"Failed to register task owned by agent ID '{task_agent_id}' against "
                f"agent ID '{agent_id}'."
            )
        )


class TaskNotFoundError(TasksServiceError):
    """Raised when a task is not found."""

    code = "TASK_NOT_FOUND_ERROR"

    def __init__(self, task_id: str) -> None:
        super().__init__(
            message=(
                "Failed to find the requested task. No task was found with the "
                f"provided task ID '{task_id}'."
            ),
        )


class TaskNotDeletableError(TasksServiceError):
    """Raised when task deletion targets a task that is still running."""

    code = "TASK_NOT_DELETABLE_ERROR"

    def __init__(self, task_str: str, state: TaskState) -> None:
        super().__init__(
            message=(
                f"Failed to delete task {task_str}. Its current state is '{state}', "
                "and a running task cannot be deleted. Wait for it to reach SUCCEEDED, "
                "FAILED, or ERRORED before deleting it."
            )
        )
