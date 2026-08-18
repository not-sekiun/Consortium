import asyncio
import uuid

import pytest
from loguru import logger

from consortium.framework.agents._task_messages_queue import TaskMessagesQueue
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.event_hooks.event_type import EventType
from consortium.server import server_singletons
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.task_objects import Task, TaskState
from consortium.server.services.task_runtime_service import TaskRuntimeService
from consortium.server.services.tasks_service import TasksService

pytestmark = pytest.mark.anyio


# These tests drive the real capability handler created by _start_agent_capability. The
# handler owns every terminal transition for a task, so the cases that matter are the
# ones where something else (agent teardown, a record deletion) acts on the task while
# the handler is suspended inside the capability. Cancellation is the mechanism that is
# supposed to stop the handler, but asyncio cancellation is an exception thrown into the
# coroutine rather than a forcible kill, so a capability can suppress it and resume.


class _RecordingEventsService:
    def __init__(self):
        self.events: list[EventType] = []

    async def trigger_event(self, event_type: EventType, **_kwargs):
        self.events.append(event_type)


class _StubCapability:
    # Duck typed to the surface _agent_capability_task_handler actually uses: a name, an
    # inbox, an outbox, channels and execute(). Subclassing BaseAgentCapability would
    # drag in component registration and the agent file manager, none of which the
    # handler touches, and would put the framework's own execute() wrapper between the
    # test and the behaviour under test.
    name = "stub_cmd"

    def __init__(self, agent: Agent, task: Task):
        self.agent = agent
        self.task = task
        self._task_messages_inbox = TaskMessagesQueue()
        self._task_messages_outbox = TaskMessagesQueue(
            queue_activity_notifier=agent._outbox_activity
        )
        self.channels = {}
        self.started = asyncio.Event()

    async def execute(self, task_launch_message: TaskLaunchMessageModel):
        raise NotImplementedError


class _PropagatingCapability(_StubCapability):
    # The contract every capability is expected to honour: let cancellation through.
    async def execute(self, task_launch_message: TaskLaunchMessageModel):
        self.started.set()
        await asyncio.Event().wait()
        return Success(message="unreachable")


class _SwallowingCapability(_StubCapability):
    # Suppresses its own cancellation and reports success anyway. Without a guard the
    # handler would resume and drive a terminal transition for a task that teardown has
    # already errored or that no longer has a record.
    async def execute(self, task_launch_message: TaskLaunchMessageModel):
        self.started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            return Success(message="swallowed the cancellation")
        return Success(message="unreachable")


class _SwallowingThenRaisingCapability(_StubCapability):
    # Suppresses the cancellation and then fails while cleaning up, so execute() raises
    # an ordinary exception and the handler's last-resort error path runs instead of the
    # normal outcome path.
    async def execute(self, task_launch_message: TaskLaunchMessageModel):
        self.started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            raise ValueError("cleanup blew up") from None


class _ImmediateCapability(_StubCapability):
    async def execute(self, task_launch_message: TaskLaunchMessageModel):
        self.started.set()
        return Success(message="done")


class _FailingCapability(_StubCapability):
    async def execute(self, task_launch_message: TaskLaunchMessageModel):
        self.started.set()
        return Failure(message="deliberate failure")


@pytest.fixture
def events_service(monkeypatch):
    recording_events_service = _RecordingEventsService()
    # The handler reaches the events service through the singletons module rather than
    # through the agent, so it has to be replaced there.
    monkeypatch.setattr(
        server_singletons, "events_service", recording_events_service, raising=False
    )
    return recording_events_service


@pytest.fixture
def warnings_and_errors():
    records = []
    sink_id = logger.add(
        lambda message: records.append(message.record), level="WARNING"
    )
    yield records
    logger.remove(sink_id)


def _make_agent() -> Agent:
    # A bare instance wired with only what the handler and record store need. A fully
    # constructed Agent requires a configured listener, payload and agent type.
    task_runtime_service = TaskRuntimeService()
    tasks_service = TasksService(
        events_service=_RecordingEventsService(),
        task_runtime_service=task_runtime_service,
    )
    agent = Agent.__new__(Agent)
    agent.agent_id = uuid.uuid4()
    agent.name = "mock-agent"
    agent.logger = logger
    agent._tasks_service = tasks_service
    agent._task_runtime_service = task_runtime_service
    agent._outbox_activity = asyncio.Condition()
    agent._new_task_started_event = asyncio.Event()
    return agent


async def _start(
    agent: Agent,
    capability_class: type[_StubCapability],
) -> tuple[Task, asyncio.Task]:
    task = Task(agent_id=agent.agent_id, command="stub_cmd", arguments={})
    agent._tasks_service._register_task(task=task, agent=agent)
    await agent._start_agent_capability(agent_capability=capability_class, task=task)
    runtime = agent._task_runtime_service.get_task_runtime(task_id=task.task_id)
    handler = runtime.handler
    # Let the capability reach its first suspension point so the scenarios below act on
    # a genuinely in-flight capability rather than one that has not started.
    await asyncio.sleep(0)
    return task, handler


async def _settle(handler: asyncio.Task) -> None:
    await asyncio.gather(handler, return_exceptions=True)
    await asyncio.sleep(0)


# --- cancellation during agent teardown ---


async def test_capability_that_propagates_cancellation_keeps_the_teardown_outcome(
    events_service,
):
    agent = _make_agent()
    task, handler = await _start(agent, _PropagatingCapability)

    agent._tasks_service._error_pending_tasks_for_agent(
        agent=agent,
        error_message="agent removed",
    )
    await _settle(handler)

    assert handler.cancelled()
    assert task.status.state == TaskState.ERRORED
    # The handler died before its transition block, so it never claims the task
    # completed.
    assert EventType.AGENT_TASK_COMPLETED not in events_service.events


async def test_capability_that_swallows_cancellation_cannot_overwrite_teardown(
    events_service,
):
    agent = _make_agent()
    task, handler = await _start(agent, _SwallowingCapability)

    agent._tasks_service._error_pending_tasks_for_agent(
        agent=agent,
        error_message="agent removed",
    )
    await _settle(handler)

    # The capability returned Success, but the task was already errored by teardown and
    # the handler must not overwrite that.
    assert task.status.state == TaskState.ERRORED
    assert EventType.AGENT_TASK_COMPLETED not in events_service.events


async def test_capability_that_swallows_cancellation_is_reported(warnings_and_errors):
    # A capability that suppresses its own cancellation is a component bug. The
    # framework recovers from it, but silently recovering would leave it undiagnosable,
    # so the capability and task have to be named in a warning.
    agent = _make_agent()
    task, handler = await _start(agent, _SwallowingCapability)

    agent._tasks_service._error_pending_tasks_for_agent(
        agent=agent,
        error_message="agent removed",
    )
    await _settle(handler)

    warnings = [
        record
        for record in warnings_and_errors
        if record["level"].name == "WARNING" and "cancel" in record["message"].lower()
    ]
    assert warnings, "expected a warning naming the capability that swallowed cancel"
    assert any(_StubCapability.name in record["message"] for record in warnings)
    assert any(str(task.task_id) in record["message"] for record in warnings)


async def test_capability_that_swallows_cancellation_then_raises_does_not_double_error(
    warnings_and_errors,
):
    # execute() raising means the guard is skipped and the handler's last-resort error
    # path runs against a task teardown already errored. That must be a declined
    # transition, not an illegal-transition AssertionError.
    agent = _make_agent()
    task, handler = await _start(agent, _SwallowingThenRaisingCapability)

    agent._tasks_service._error_pending_tasks_for_agent(
        agent=agent,
        error_message="agent removed",
    )
    await _settle(handler)

    assert task.status.state == TaskState.ERRORED
    # The teardown error is the one that survives, not the capability's cleanup failure.
    assert "agent removed" in str(task.status.error.message)
    assert not any(
        "AssertionError" in str(record["message"]) for record in warnings_and_errors
    )


# --- cancellation during record deletion ---


async def test_deleting_a_task_stops_a_capability_that_swallows_cancellation(
    events_service,
):
    agent = _make_agent()
    task, handler = await _start(agent, _SwallowingCapability)

    await agent._tasks_service.delete_task_by_task_id(task_id=task.task_id)
    await _settle(handler)

    # The record is gone and the orphaned task object is left exactly as deletion found
    # it: never transitioned, and never announced as completed.
    assert agent._tasks_service.find_task(task_id=task.task_id) is None
    assert task.status.state == TaskState.QUEUED
    assert EventType.AGENT_TASK_COMPLETED not in events_service.events


# --- normal completion ---


async def test_handler_completing_normally_transitions_and_announces(events_service):
    agent = _make_agent()
    task, handler = await _start(agent, _ImmediateCapability)

    await _settle(handler)

    assert task.status.state == TaskState.SUCCEEDED
    assert task.datetime_completed is not None
    assert EventType.AGENT_TASK_COMPLETED in events_service.events
    # The inbox is released on completion because no further results can be routed to
    # it, while the outbox stays attached so buffered output is still drainable.
    runtime = agent._task_runtime_service.get_task_runtime(task_id=task.task_id)
    assert runtime is not None
    assert runtime.inbox is None
    assert runtime.outbox is not None


async def test_handler_reports_a_deliberate_failure_as_failed(events_service):
    agent = _make_agent()
    task, handler = await _start(agent, _FailingCapability)

    await _settle(handler)

    assert task.status.state == TaskState.FAILED
    assert EventType.AGENT_TASK_COMPLETED in events_service.events


async def test_completion_that_lands_before_a_delete_still_announces(events_service):
    # The handler finished and the task genuinely succeeded, so the completion is
    # factually true even though the operator deleted the record immediately after.
    agent = _make_agent()
    task, handler = await _start(agent, _ImmediateCapability)
    await _settle(handler)

    await agent._tasks_service.delete_task_by_task_id(task_id=task.task_id)

    assert agent._tasks_service.find_task(task_id=task.task_id) is None
    assert EventType.AGENT_TASK_COMPLETED in events_service.events
