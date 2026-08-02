import asyncio
import uuid

import pytest

from consortium.framework.agents._task_messages_queue import (
    END_OF_STREAM,
    TaskMessagesQueue,
)
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.tasks_service_exceptions import (
    TaskNotDeletableError,
    TaskNotFoundError,
)
from consortium.server.models.task_models import TaskState
from consortium.server.objects.task_objects import Task
from consortium.server.objects.task_runtime import TaskRuntime
from consortium.server.services.task_runtime_service import TaskRuntimeService
from consortium.server.services.tasks_service import TasksService
from consortium.server.utils import utc_now

pytestmark = pytest.mark.anyio


class _RecordingEventsService:
    # Captures the events the service emits so tests can assert on the payload a client
    # would actually receive, in particular the task state carried by TASK_DELETED.
    def __init__(self):
        self.events: list[tuple[EventType, dict]] = []

    async def trigger_event(self, event_type: EventType, message: str, data, **_kwargs):
        self.events.append((event_type, data))

    def events_of_type(self, event_type: EventType) -> list[dict]:
        return [data for recorded, data in self.events if recorded is event_type]


class _StubAgent:
    # TasksService only ever reads agent_id off the owner and formats it into log
    # messages, so a full Agent (which needs a configured listener, payload and agent
    # type) is not required to exercise the record store.
    def __init__(self):
        self.agent_id = uuid.uuid4()

    def __str__(self) -> str:
        return f"StubAgent({self.agent_id})"


def _make_services(
    max_retained_terminal_tasks: int = 100,
) -> tuple[TasksService, TaskRuntimeService, _RecordingEventsService]:
    events_service = _RecordingEventsService()
    task_runtime_service = TaskRuntimeService()
    tasks_service = TasksService(
        events_service=events_service,
        task_runtime_service=task_runtime_service,
        max_retained_terminal_tasks=max_retained_terminal_tasks,
    )
    return tasks_service, task_runtime_service, events_service


def _register_task(
    tasks_service: TasksService,
    agent: _StubAgent,
    command: str = "mock_cmd",
) -> Task:
    task = Task(agent_id=agent.agent_id, command=command, arguments={})
    tasks_service._register_task(task=task, agent=agent)
    return task


def _attach_runtime(
    task_runtime_service: TaskRuntimeService,
    task: Task,
    agent: _StubAgent,
    handler: asyncio.Task | None = None,
) -> tuple[TaskMessagesQueue, TaskMessagesQueue]:
    inbox = TaskMessagesQueue()
    outbox = TaskMessagesQueue()
    runtime = TaskRuntime()
    runtime.attach(handler=handler, inbox=inbox, outbox=outbox)
    task_runtime_service.attach_task_runtime(
        task_id=task.task_id,
        agent_id=agent.agent_id,
        task_runtime=runtime,
    )
    return inbox, outbox


# --- record store queries ---


async def test_registered_tasks_are_queryable_by_owner_and_state():
    tasks_service, _, _ = _make_services()
    first_agent = _StubAgent()
    second_agent = _StubAgent()
    queued_task = _register_task(tasks_service, first_agent)
    running_task = _register_task(tasks_service, first_agent)
    running_task.status._transition_to_running()
    other_task = _register_task(tasks_service, second_agent)

    assert tasks_service.get_all_tasks(agent_id=first_agent.agent_id) == [
        queued_task,
        running_task,
    ]
    assert tasks_service.get_all_tasks(
        agent_id=first_agent.agent_id,
        status=TaskState.RUNNING,
    ) == [running_task]
    assert tasks_service.get_all_tasks(agent_id=second_agent.agent_id) == [other_task]
    # Lookups are canonicalized, so a differently cased ID still resolves.
    assert (
        tasks_service.get_task_by_task_id(task_id=str(queued_task.task_id).upper())
        is queued_task
    )


async def test_find_task_scopes_by_owner_and_state():
    tasks_service, _, _ = _make_services()
    agent = _StubAgent()
    other_agent = _StubAgent()
    task = _register_task(tasks_service, agent)

    assert tasks_service.find_task(task_id=task.task_id) is task
    assert (
        tasks_service.find_task(task_id=task.task_id, agent_id=agent.agent_id) is task
    )
    assert (
        tasks_service.find_task(task_id=task.task_id, agent_id=other_agent.agent_id)
        is None
    )
    assert (
        tasks_service.find_task(task_id=task.task_id, status=TaskState.RUNNING) is None
    )
    # A non-UUID is reported as absent rather than as a malformed-input error.
    assert tasks_service.find_task(task_id="not-a-uuid") is None


async def test_get_task_by_task_id_raises_for_unknown_and_malformed_ids():
    tasks_service, _, _ = _make_services()

    with pytest.raises(TaskNotFoundError):
        tasks_service.get_task_by_task_id(task_id=uuid.uuid4())
    with pytest.raises(TaskNotFoundError):
        tasks_service.get_task_by_task_id(task_id="not-a-uuid")


# --- deletion ---


async def test_deleting_a_queued_task_destroys_the_record_and_its_runtime():
    tasks_service, task_runtime_service, events_service = _make_services()
    agent = _StubAgent()
    task = _register_task(tasks_service, agent)
    handler = asyncio.create_task(asyncio.Event().wait())
    inbox, outbox = _attach_runtime(task_runtime_service, task, agent, handler=handler)

    await tasks_service.delete_task_by_task_id(task_id=task.task_id)
    await asyncio.sleep(0)

    assert tasks_service.find_task(task_id=task.task_id) is None
    assert task_runtime_service.get_task_runtime(task_id=task.task_id) is None
    assert handler.cancelled()
    # Immediate shutdown, so a reader parked on either queue observes end of stream
    # rather than the deleted task's buffered output.
    assert await inbox.get(timeout=0) is END_OF_STREAM
    assert await outbox.get(timeout=0) is END_OF_STREAM


async def test_deleting_a_queued_task_reports_it_as_queued_in_the_event():
    # Deletion never transitions the record. A task deleted before the agent picked it
    # up is reported as QUEUED, which is the truthful account: it never ran.
    tasks_service, task_runtime_service, events_service = _make_services()
    agent = _StubAgent()
    task = _register_task(tasks_service, agent)
    _attach_runtime(task_runtime_service, task, agent)

    await tasks_service.delete_task_by_task_id(task_id=task.task_id)
    await asyncio.sleep(0)

    deleted_events = events_service.events_of_type(EventType.TASK_DELETED)
    assert len(deleted_events) == 1
    assert deleted_events[0]["status"]["state"] == TaskState.QUEUED


@pytest.mark.parametrize(
    "terminal_state",
    [TaskState.SUCCEEDED, TaskState.FAILED, TaskState.ERRORED],
)
async def test_terminal_tasks_are_deletable(terminal_state):
    tasks_service, task_runtime_service, _ = _make_services()
    agent = _StubAgent()
    task = _register_task(tasks_service, agent)
    if terminal_state is TaskState.SUCCEEDED:
        task.status._transition_to_succeeded()
    else:
        task.status._transition_to_state(new_state=terminal_state, error=_an_error())
    _attach_runtime(task_runtime_service, task, agent)

    await tasks_service.delete_task_by_task_id(task_id=task.task_id)

    assert tasks_service.find_task(task_id=task.task_id) is None


async def test_deleting_a_running_task_is_rejected_and_changes_nothing():
    tasks_service, task_runtime_service, events_service = _make_services()
    agent = _StubAgent()
    task = _register_task(tasks_service, agent)
    task.status._transition_to_running()
    inbox, outbox = _attach_runtime(task_runtime_service, task, agent)

    with pytest.raises(TaskNotDeletableError):
        await tasks_service.delete_task_by_task_id(task_id=task.task_id)

    assert tasks_service.find_task(task_id=task.task_id) is task
    assert task_runtime_service.get_task_runtime(task_id=task.task_id) is not None
    assert events_service.events_of_type(EventType.TASK_DELETED) == []
    # A rejected delete must not have torn down anything the task is still using. An
    # open but empty queue reports "nothing yet" by timing out, which is distinct from
    # the END_OF_STREAM a shut down queue returns.
    with pytest.raises(TimeoutError):
        await inbox.get(timeout=0)
    with pytest.raises(TimeoutError):
        await outbox.get(timeout=0)


async def test_deleting_an_unknown_task_raises_not_found():
    tasks_service, _, _ = _make_services()

    with pytest.raises(TaskNotFoundError):
        await tasks_service.delete_task_by_task_id(task_id=uuid.uuid4())


async def test_concurrent_deletes_destroy_the_record_exactly_once():
    # The record pop is the single point that decides who owns teardown, so two racing
    # deletes must produce one TASK_DELETED and one queue shutdown between them.
    tasks_service, task_runtime_service, events_service = _make_services()
    agent = _StubAgent()
    task = _register_task(tasks_service, agent)
    _attach_runtime(task_runtime_service, task, agent)

    results = await asyncio.gather(
        tasks_service.delete_task_by_task_id(task_id=task.task_id),
        tasks_service.delete_task_by_task_id(task_id=task.task_id),
        return_exceptions=True,
    )
    await asyncio.sleep(0)

    # The loser either finds the record already gone or completes as a no-op, but it
    # must never raise anything other than TaskNotFoundError.
    for result in results:
        assert result is None or isinstance(result, TaskNotFoundError)
    assert len(events_service.events_of_type(EventType.TASK_DELETED)) == 1
    assert tasks_service.find_task(task_id=task.task_id) is None


async def test_deletion_prevents_a_later_promotion_to_running():
    # A reader that dequeued a launch message before the delete must not be able to
    # promote the task afterwards: a deleted task that is reported RUNNING would mean
    # the operator got a 204 for a task the agent had actually picked up.
    tasks_service, task_runtime_service, _ = _make_services()
    agent = _StubAgent()
    task = _register_task(tasks_service, agent)
    _attach_runtime(task_runtime_service, task, agent)

    await tasks_service.delete_task_by_task_id(task_id=task.task_id)

    assert task.status._try_transition_to_running() is False
    assert task.status.state == TaskState.QUEUED


# --- agent teardown ---


async def test_error_pending_tasks_errors_queued_and_running_and_keeps_records():
    tasks_service, task_runtime_service, _ = _make_services()
    agent = _StubAgent()
    queued_task = _register_task(tasks_service, agent)
    running_task = _register_task(tasks_service, agent)
    running_task.status._transition_to_running()
    handler = asyncio.create_task(asyncio.Event().wait())
    inbox, outbox = _attach_runtime(
        task_runtime_service, running_task, agent, handler=handler
    )

    errored_tasks = tasks_service._error_pending_tasks_for_agent(
        agent=agent,
        error_message="agent removed",
    )
    await asyncio.sleep(0)

    assert set(errored_tasks) == {queued_task, running_task}
    for task in (queued_task, running_task):
        # Records outlive the agent so the operator can still read what happened.
        assert tasks_service.find_task(task_id=task.task_id) is task
        assert task.status.state == TaskState.ERRORED
        assert task.datetime_completed is not None
        assert task_runtime_service.get_task_runtime(task_id=task.task_id) is None
    assert handler.cancelled()
    assert await inbox.get(timeout=0) is END_OF_STREAM
    assert await outbox.get(timeout=0) is END_OF_STREAM


async def test_error_pending_tasks_leaves_already_terminal_tasks_alone():
    tasks_service, _, _ = _make_services()
    agent = _StubAgent()
    succeeded_task = _register_task(tasks_service, agent)
    succeeded_task.status._transition_to_succeeded()
    completed_at = utc_now()
    succeeded_task.datetime_completed = completed_at

    errored_tasks = tasks_service._error_pending_tasks_for_agent(
        agent=agent,
        error_message="agent removed",
    )

    # A task that already reached a terminal state is not reported as errored and its
    # recorded outcome is preserved exactly.
    assert errored_tasks == []
    assert succeeded_task.status.state == TaskState.SUCCEEDED
    assert succeeded_task.datetime_completed == completed_at


async def test_error_pending_tasks_only_touches_the_removed_agents_tasks():
    tasks_service, _, _ = _make_services()
    removed_agent = _StubAgent()
    surviving_agent = _StubAgent()
    removed_task = _register_task(tasks_service, removed_agent)
    surviving_task = _register_task(tasks_service, surviving_agent)

    tasks_service._error_pending_tasks_for_agent(
        agent=removed_agent,
        error_message="agent removed",
    )

    assert removed_task.status.state == TaskState.ERRORED
    assert surviving_task.status.state == TaskState.QUEUED


# --- terminal task retention ---


async def test_retention_evicts_the_oldest_terminal_task_and_its_runtime():
    tasks_service, task_runtime_service, events_service = _make_services(
        max_retained_terminal_tasks=1
    )
    agent = _StubAgent()
    oldest_task = _register_task(tasks_service, agent)
    oldest_task.status._transition_to_succeeded()
    oldest_task.datetime_completed = utc_now()
    _, oldest_outbox = _attach_runtime(task_runtime_service, oldest_task, agent)
    newest_task = _register_task(tasks_service, agent)
    newest_task.status._transition_to_succeeded()
    newest_task.datetime_completed = utc_now()

    # Registration is what enforces the bound, so registering a third task triggers it.
    _register_task(tasks_service, agent)
    await asyncio.sleep(0)

    assert tasks_service.find_task(task_id=oldest_task.task_id) is None
    assert tasks_service.find_task(task_id=newest_task.task_id) is newest_task
    assert task_runtime_service.get_task_runtime(task_id=oldest_task.task_id) is None
    assert await oldest_outbox.get(timeout=0) is END_OF_STREAM
    assert len(events_service.events_of_type(EventType.TASK_DELETED)) == 1


async def test_retention_never_evicts_a_pending_task():
    tasks_service, _, _ = _make_services(max_retained_terminal_tasks=0)
    agent = _StubAgent()
    queued_task = _register_task(tasks_service, agent)
    running_task = _register_task(tasks_service, agent)
    running_task.status._transition_to_running()

    _register_task(tasks_service, agent)

    assert tasks_service.find_task(task_id=queued_task.task_id) is queued_task
    assert tasks_service.find_task(task_id=running_task.task_id) is running_task


def _an_error():
    from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (  # noqa: E501
        AgentCapabilityExecutionError,
    )

    return AgentCapabilityExecutionError(
        agent_capability_name="mock_cmd",
        error_message="mock failure",
    )
