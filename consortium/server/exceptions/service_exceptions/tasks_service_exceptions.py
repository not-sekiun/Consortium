from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class TasksServiceError(BaseServiceError):
    """Base exception for all errors that occur within the tasks service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "TASKS_SERVICE_ERROR"


class TaskNotFoundError(BaseServiceError):
    """Raised when a task is not found."""

    code = "TASK_NOT_FOUND"

    def __init__(self, task_id: str) -> None:
        super().__init__(
            message=(
                "Failed to find the requested task. No task was found with the "
                f"provided task ID '{task_id}'."
            ),
        )


class TaskCurrentlyRunningError(BaseServiceError):
    """Raised when an operation is attempted on a task that requires it to not be
    running but the task is currently running."""

    code = "TASK_CURRENTLY_RUNNING"

    def __init__(self, task_str: str) -> None:
        super().__init__(
            message=(
                f"Failed to perform the requested operation on the task {task_str}"
                "The task is currently running and must reach a terminal state before "
                "that operation can be executed."
            )
        )
