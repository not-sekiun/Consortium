import uuid
import weakref
from typing import TYPE_CHECKING

from loguru import logger

from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.object_exceptions.agent_object_exceptions import (
    AgentTaskNotFoundError,
)
from consortium.server.exceptions.service_exceptions.tasks_service_exceptions import (
    TaskAgentMismatchError,
    TaskNotFoundError,
    TaskNotQueuedError,
    TaskNotTerminalError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.models.task_models import TaskState
from consortium.server.objects.task_objects import Task
from consortium.server.services.events_service import EventsService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
    run_async_background_task,
)

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent


TERMINAL_TASK_STATES = frozenset(
    {
        TaskState.SUCCEEDED,
        TaskState.FAILED,
        TaskState.ERRORED,
    }
)
DEFAULT_MAX_RETAINED_TERMINAL_TASKS = 1000


def _canonicalize_uuid(value: str | uuid.UUID) -> str | None:
    # Task and agent IDs are stored as canonical lowercase UUID strings, so a lookup
    # value has to be canonicalized before it is compared against them. This is local
    # to this service rather than folded into normalize_uuid because the shared helper
    # is called by every other service with identifiers that are not always UUIDs, and
    # raising there would turn their not-found errors into unhandled ValueErrors.
    # Returns None when the value is not a UUID at all, which callers treat as "no
    # such record" rather than as an error.
    try:
        return str(uuid.UUID(str(value)))
    except ValueError:
        return None


class TasksService:
    def __init__(
        self,
        events_service: EventsService,
        max_retained_terminal_tasks: int = DEFAULT_MAX_RETAINED_TERMINAL_TASKS,
    ):
        if max_retained_terminal_tasks < 0:
            raise ValueError("max_retained_terminal_tasks must be non-negative")

        self._events_service = events_service
        self._max_retained_terminal_tasks = max_retained_terminal_tasks
        self._tasks: dict[str, Task] = {}
        # Runtime owner references are weak so the global task registry never keeps a
        # deleted agent alive solely because one of its task records still exists.
        self._task_agents: weakref.WeakValueDictionary[str, Agent] = (
            weakref.WeakValueDictionary()
        )
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self):
        return "TasksService"

    def __repr__(self):
        return "TasksService()"

    @log_and_propagate_error_on_service_method
    def register_task(self, task: Task, agent: Agent) -> Task:
        """Registers a task globally while retaining a weak runtime owner reference."""
        if task.agent_id != agent.agent_id:
            raise TaskAgentMismatchError(
                task_agent_id=str(task.agent_id),
                agent_id=str(agent.agent_id),
            )

        task_id = str(task.task_id)
        self._tasks[task_id] = task
        self._task_agents[task_id] = agent
        self._logger.debug("Registered task {} for agent {}", task, agent)
        # Registration is the only point at which the registry grows, so it is where
        # the retention bound is enforced. Keeping this here rather than calling into
        # the service from the capability handler leaves eviction entirely owned by
        # this service.
        self._prune_terminal_tasks()
        return task

    @log_and_propagate_error_on_service_method
    def get_all_tasks(
        self,
        agent_id: str | uuid.UUID | None = None,
        status: TaskState | None = None,
    ) -> list[Task]:
        """Returns globally registered tasks filtered by owner and/or state."""
        if agent_id is None:
            normalized_agent_id = None
        else:
            normalized_agent_id = _canonicalize_uuid(value=agent_id)
            # A filter value that is not a UUID can never match a stored agent ID.
            if normalized_agent_id is None:
                self._logger.debug(
                    "Retrieved no tasks: agent ID filter {} is not a valid UUID",
                    agent_id,
                )
                return []

        tasks = [
            task
            for task in self._tasks.values()
            if (
                normalized_agent_id is None or str(task.agent_id) == normalized_agent_id
            )
            and (status is None or task.status.state == status)
        ]
        self._logger.debug(
            "Retrieved tasks with agent ID {} and status {} ({} retrieved)",
            normalized_agent_id,
            status,
            len(tasks),
        )
        return tasks

    @log_and_propagate_error_on_service_method
    def get_task_by_task_id(self, task_id: str | uuid.UUID) -> Task:
        """Returns a globally registered task by its ID."""
        normalized_task_id = _canonicalize_uuid(value=task_id)
        # A task ID that is not a UUID can never identify a stored task, so it is
        # reported as not found rather than as a malformed-input error.
        if normalized_task_id is None:
            raise TaskNotFoundError(task_id=normalize_uuid(value=task_id))

        try:
            task = self._tasks[normalized_task_id]
        except KeyError:
            raise TaskNotFoundError(task_id=normalized_task_id) from None

        self._logger.debug("Retrieved task {}", task)
        return task

    @log_and_propagate_error_on_service_method
    async def delete_queued_task_by_task_id(self, task_id: str | uuid.UUID) -> None:
        """Deletes a QUEUED task and tears down its agent-side runtime state."""
        task = self.get_task_by_task_id(task_id=task_id)
        if task.status.state != TaskState.QUEUED:
            raise TaskNotQueuedError(task_str=str(task), state=task.status.state)

        normalized_task_id = str(task.task_id)
        agent = self._task_agents.get(normalized_task_id)
        if agent is not None:
            try:
                await agent.delete_queued_task_by_task_id(task_id=normalized_task_id)
            except AgentTaskNotFoundError:
                # A concurrent deletion may have already torn down the agent-side
                # runtime. The global task record still needs to be reaped.
                pass

        self._delete_task_record(task=task)

    @log_and_propagate_error_on_service_method
    async def delete_terminal_task_by_task_id(self, task_id: str | uuid.UUID) -> None:
        """Deletes a task that has reached SUCCEEDED, FAILED, or ERRORED."""
        task = self.get_task_by_task_id(task_id=task_id)
        if task.status.state not in TERMINAL_TASK_STATES:
            raise TaskNotTerminalError(task_str=str(task), state=task.status.state)

        normalized_task_id = str(task.task_id)
        agent = self._task_agents.get(normalized_task_id)
        if agent is not None:
            try:
                await agent.delete_terminal_task_by_task_id(task_id=normalized_task_id)
            except AgentTaskNotFoundError:
                # A concurrent deletion may have already torn down the agent-side
                # runtime. The global task record still needs to be reaped.
                pass

        self._delete_task_record(task=task)

    @log_and_propagate_error_on_service_method
    def error_pending_tasks_for_agent(
        self,
        agent: Agent,
        error_message: str,
    ) -> list[Task]:
        """Transitions an agent's queued and running tasks to ERRORED."""
        errored_tasks = agent.error_pending_tasks(error_message=error_message)
        self._logger.debug(
            "Marked {} pending task(s) as ERRORED because agent {} was removed",
            len(errored_tasks),
            agent,
        )
        # These tasks just became terminal, so they are now eligible for eviction.
        self._prune_terminal_tasks()
        return errored_tasks

    def _prune_terminal_tasks(self) -> None:
        terminal_tasks = [
            task
            for task in self._tasks.values()
            if task.status.state in TERMINAL_TASK_STATES
        ]
        excess_count = len(terminal_tasks) - self._max_retained_terminal_tasks
        if excess_count <= 0:
            return

        terminal_tasks.sort(
            key=lambda task: task.datetime_completed or task.datetime_created
        )
        for task in terminal_tasks[:excess_count]:
            self._logger.debug(
                "Evicting retained terminal task {} after exceeding the limit of {}",
                task,
                self._max_retained_terminal_tasks,
            )
            task_id = str(task.task_id)
            agent = self._task_agents.get(task_id)
            if agent is not None:
                run_async_background_task(
                    self._delete_evicted_task_from_agent(
                        agent=agent,
                        task_id=task_id,
                    )
                )
            self._delete_task_record(task=task)

    @staticmethod
    async def _delete_evicted_task_from_agent(agent: Agent, task_id: str) -> None:
        try:
            await agent.delete_terminal_task_by_task_id(task_id=task_id)
        except AgentTaskNotFoundError:
            pass

    def _delete_task_record(self, task: Task) -> None:
        task_id = str(task.task_id)
        deleted_task = self._tasks.pop(task_id, None)
        self._task_agents.pop(task_id, None)
        if deleted_task is None:
            return

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.TASK_DELETED,
                message=f"Deleted task: {deleted_task}",
                data=deleted_task.to_json(),
            )
        )
        self._logger.debug("Deleted task {}", deleted_task)
