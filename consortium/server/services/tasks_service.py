import uuid

from loguru import logger

from consortium.server.exceptions.service_exceptions.tasks_service_exceptions import (
    TaskCurrentlyRunningError,
    TaskNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.models.task_models import (
    TaskState,
)
from consortium.server.objects.task_objects import Task
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class TasksService:
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self):
        return "TasksService"

    def __repr__(self):
        return "TasksService()"

    @log_and_propagate_error_on_service_method
    def get_all_tasks(self, status: TaskState | None = None) -> list[Task]:
        """Returns all tasks across every registered agent, optionally filtered by
        state.

        Args:
            status: When provided, only tasks in this state are
                returned. When `None`, all tasks regardless of state are returned.

        Returns:
            A list of matching tasks. Empty if no tasks match.
        """
        if status is None:
            all_tasks = list(self._tasks.values())
            self._logger.debug(
                "Retrieved all tasks from all agents ({} retrieved)",
                len(all_tasks),
            )
        else:
            all_tasks = [
                task for task in self._tasks.values() if task.status.state == status
            ]
            self._logger.debug(
                "Retrieved all tasks from all agents with status {} ({} retrieved)",
                status,
                len(all_tasks),
            )
        return all_tasks

    @log_and_propagate_error_on_service_method
    def get_task_by_task_id(self, task_id: str | uuid.UUID) -> Task:
        """Returns a task by its ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            The task with the specified ID.

        Raises:
            TaskNotFoundError: If no task with the given ID exists.
        """
        task_id = normalize_uuid(task_id)

        try:
            task = self._tasks[task_id]
        except KeyError:
            raise TaskNotFoundError(task_id=task_id) from None
        self._logger.debug("Retrieved task {}", task)
        return task

    @log_and_propagate_error_on_service_method
    def delete_task_by_task_id(self, task_id: str) -> None:
        """Deletes a task by its ID.
        Args:
            task_id: The ID of the task to delete.
        """
        task = self.get_task_by_task_id(task_id)
        if task.status.state == TaskState.RUNNING:
            raise TaskCurrentlyRunningError(task_str=str(task))
        del self._tasks[task_id]
        self._logger.debug("Deleted task {}", task)
