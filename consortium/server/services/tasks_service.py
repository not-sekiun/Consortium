import uuid
from typing import TYPE_CHECKING

from loguru import logger

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCapabilityExecutionError,
)
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.tasks_service_exceptions import (
    TaskNotDeletableError,
    TaskNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.models.task_models import TaskState
from consortium.server.objects.task_objects import Task
from consortium.server.services.events_service import EventsService
from consortium.server.services.task_runtime_service import TaskRuntimeService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
    run_async_background_task,
    utc_now,
)

if TYPE_CHECKING:
    from consortium.framework.agents._memory_bounded_buffer import MemoryBoundedBuffer
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
        task_runtime_service: TaskRuntimeService,
        max_retained_terminal_tasks: int = DEFAULT_MAX_RETAINED_TERMINAL_TASKS,
    ):
        if max_retained_terminal_tasks < 0:
            raise ValueError("max_retained_terminal_tasks must be non-negative")

        self._events_service = events_service
        self._task_runtime_service = task_runtime_service
        self._max_retained_terminal_tasks = max_retained_terminal_tasks
        self._tasks: dict[str, Task] = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self):
        return "TasksService"

    def __repr__(self):
        return "TasksService()"

    @log_and_propagate_error_on_service_method
    def get_all_tasks(
        self,
        agent_id: str | uuid.UUID | None = None,
        status: TaskState | None = None,
    ) -> list[Task]:
        """Returns global task records filtered by owner and/or state.

        Args:
            agent_id: The ID of the agent whose tasks to return. When `None`, tasks
                are not filtered by owner. A value that is not a valid UUID matches
                no tasks.
            status: The task state to filter by. When `None`, tasks are not
                filtered by state.

        Returns:
            The matching task records. Empty if none match, or if `agent_id` is not
            a valid UUID.
        """
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
        """Returns a global task record by its ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            The requested task record.

        Raises:
            TaskNotFoundError: If no task with the given ID exists.
        """
        task = self.find_task(task_id=task_id)
        if task is None:
            normalized_task_id = _canonicalize_uuid(value=task_id)
            raise TaskNotFoundError(
                task_id=normalized_task_id or normalize_uuid(value=task_id)
            )

        self._logger.debug("Retrieved task {}", task)
        return task

    def _destroy_task_record(self, task: Task) -> list[MemoryBoundedBuffer]:
        # The only place a record is ever removed, which is what keeps a runtime from
        # outliving its record: popping both here in one synchronous block makes that
        # impossible by construction. Any new removal path has to do the same.
        # The record is popped before the runtime is touched so that a racing second
        # caller returns empty handed rather than detaching queues it will not shut
        # down.
        task_id = str(task.task_id)
        deleted_task = self._tasks.pop(task_id, None)
        if deleted_task is None:
            return []

        runtime = self._task_runtime_service.pop(task_id=task_id)
        buffers = runtime.detach() if runtime is not None else []
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.TASK_DELETED,
                message=f"Deleted task: {deleted_task}",
                data=deleted_task.to_json(),
            )
        )
        self._logger.debug("Deleted task {}", deleted_task)
        return buffers

    @staticmethod
    async def _shutdown_buffers(buffers: list[MemoryBoundedBuffer]) -> None:
        # Immediate shutdown drops what is buffered and wakes readers already blocked
        # in get() so they observe end of stream instead of deleted task output.
        for buffer in buffers:
            await buffer.shutdown(immediate=True)

    @log_and_propagate_error_on_service_method
    async def delete_task_by_task_id(self, task_id: str | uuid.UUID) -> None:
        """Deletes a task that is not RUNNING and tears down its runtime state.

        Args:
            task_id: The ID of the task to delete.

        Raises:
            TaskNotFoundError: If no task with the given ID exists.
            TaskNotDeletableError: If the task is currently RUNNING.
        """
        task = self.get_task_by_task_id(task_id=task_id)
        # The claim fuses the deletability test with taking ownership, so there is no
        # gap for a reader to promote this task to RUNNING after it was judged
        # deletable: a claimed task refuses every subsequent transition. It also makes
        # the winner of two racing deletes uniquely responsible for the teardown.
        if not task.status.claim_for_deletion():
            raise TaskNotDeletableError(task_str=str(task), state=task.status.state)

        # No await may be introduced between the state check and record destruction:
        # this synchronous block closes the QUEUED-to-RUNNING deletion race. Terminal
        # states are absorbing, so a task that passes this check while terminal cannot
        # start running underneath the delete.
        buffers = self._destroy_task_record(task=task)
        await self._shutdown_buffers(buffers=buffers)

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
        buffers_to_shut_down = []
        for task in terminal_tasks[:excess_count]:
            self._logger.debug(
                "Evicting retained terminal task {} after exceeding the limit of {}",
                task,
                self._max_retained_terminal_tasks,
            )
            buffers_to_shut_down.extend(self._destroy_task_record(task=task))

        if buffers_to_shut_down:
            run_async_background_task(
                coroutine=self._shutdown_buffers(buffers=buffers_to_shut_down)
            )

    def find_task(
        self,
        task_id: str | uuid.UUID,
        agent_id: str | uuid.UUID | None = None,
        status: TaskState | None = None,
    ) -> Task | None:
        """Find a task by ID, optionally scoped to an owner and state.

        Args:
            task_id: The ID of the task to find.
            agent_id: When provided, the task is only returned if it is owned by
                this agent ID.
            status: When provided, the task is only returned if it is in this
                state.

        Returns:
            The matching task, or `None` if `task_id` is not a valid UUID, no task
            with that ID exists, or the task does not match the given `agent_id` or
            `status`.
        """
        normalized_task_id = _canonicalize_uuid(value=task_id)
        if normalized_task_id is None:
            return None

        task = self._tasks.get(normalized_task_id)
        if task is None:
            return None

        if agent_id is not None:
            normalized_agent_id = _canonicalize_uuid(value=agent_id)
            if normalized_agent_id is None or str(task.agent_id) != normalized_agent_id:
                return None

        if status is not None and task.status.state != status:
            return None

        return task

    @log_and_propagate_error_on_service_method
    def _register_task(self, task: Task, agent: Agent) -> Task:
        # Internal: the record store is only ever grown by Agent.submit_task, which
        # registers a task after its capability has started. Callers outside the
        # framework inspect and delete records, they do not create them. Ownership is
        # validated by Agent._resolve_and_validate_tasking before anything is started
        # (and before a task even exists to register), so this method
        # deliberately performs no checks that could raise after a handler exists.
        task_id = str(task.task_id)
        self._tasks[task_id] = task
        self._logger.debug("Registered task {} for agent {}", task, agent)
        # Registration is the only point at which the record store grows, so it is
        # where the retention bound is enforced. Keeping this here rather than calling
        # into the service from the capability handler leaves eviction entirely owned
        # by this service.
        self._prune_terminal_tasks()
        return task

    @log_and_propagate_error_on_service_method
    def _error_pending_tasks_for_agent(
        self,
        agent: Agent,
        error_message: str,
    ) -> list[Task]:
        # Internal: this is agent teardown, not a record operation. It is called by
        # AgentsService when an agent is removed and exposed to callers only through
        # Agent.error_pending_tasks.
        # Runtime teardown is unconditional: after the agent is gone no buffered output
        # is reachable anyway, because every drain path resolves the agent through
        # AgentsService.get_agent_by_agent_id first. Leaving any runtime attached would
        # keep the removed agent alive through outbox -> _agent.
        runtimes = self._task_runtime_service.pop_all_for_agent(agent_id=agent.agent_id)
        buffers_to_shut_down = [
            buffer for runtime in runtimes for buffer in runtime.detach()
        ]

        # The transition is a compare and swap, so a handler cancelled just above that
        # reaches its own terminal transition first is a losing racer rather than an
        # illegal-transition error that would abort agent removal partway through the
        # loop. Whoever wins, the task ends up terminal.
        errored_tasks = []
        for task in self.get_all_tasks(agent_id=agent.agent_id):
            if not task.status._try_transition_to_errored(
                error=AgentCapabilityExecutionError(
                    agent_capability_name=task.command,
                    error_message=error_message,
                )
            ):
                continue

            task.datetime_completed = utc_now()
            task.event_logger.error(
                message=error_message,
                data={"agent_id": str(agent.agent_id)},
            )
            errored_tasks.append(task)

        if buffers_to_shut_down:
            run_async_background_task(
                coroutine=self._shutdown_buffers(buffers=buffers_to_shut_down)
            )

        self._logger.debug(
            "Marked {} pending task(s) as ERRORED because agent {} was removed",
            len(errored_tasks),
            agent,
        )
        # These tasks just became terminal, so they are now eligible for eviction.
        self._prune_terminal_tasks()
        return errored_tasks
