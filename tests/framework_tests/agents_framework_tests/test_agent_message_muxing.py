import asyncio
import gc
import uuid
import weakref

import pytest
from loguru import logger

from consortium.framework.agents._task_messages_queue import (
    END_OF_STREAM,
    TaskMessagesQueue,
)
from consortium.framework.agents.agent_message_models import (
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.options import SingleValueOption
from consortium.framework.signal_exceptions.options_signal_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.object_exceptions.agent_object_exceptions import (
    AgentCapabilityNotFoundError,
    AgentCapabilityValidatingFunctionError,
    AgentTaskNotFoundError,
    MissingRequiredAgentCapabilityOptionError,
)
from consortium.server.exceptions.service_exceptions.tasks_service_exceptions import (
    TaskNotDeletableError,
)
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.task_objects import Task, TaskState
from consortium.server.objects.task_runtime import TaskRuntime
from consortium.server.services.agents_service import AgentsService
from consortium.server.services.task_runtime_service import TaskRuntimeService
from consortium.server.services.tasks_service import TasksService
from consortium.server.utils import utc_now


class _StubEventsService:
    async def trigger_event(self, **_kwargs) -> None:
        pass


def _make_agent(
    tasks_service: TasksService | None = None,
    task_runtime_service: TaskRuntimeService | None = None,
) -> Agent:
    # The task message routing methods only touch the task record store and runtime
    # registry attributes, not the listener, payload or agent type resolution that
    # Agent.__init__ performs (which needs a fully configured server). Build a bare
    # instance and wire up just those attributes so the muxing logic can be exercised
    # in isolation.
    agent = Agent.__new__(Agent)
    agent.agent_id = uuid.uuid4()
    agent.name = "mock-agent"
    agent.logger = logger
    if tasks_service is None:
        task_runtime_service = task_runtime_service or TaskRuntimeService()
        tasks_service = TasksService(
            events_service=_StubEventsService(),
            task_runtime_service=task_runtime_service,
        )
    elif task_runtime_service is None:
        task_runtime_service = tasks_service._task_runtime_service
    agent._tasks_service = tasks_service
    agent._task_runtime_service = task_runtime_service
    agent._outbox_activity = asyncio.Condition()
    agent._new_task_started_event = asyncio.Event()
    return agent


def _add_outbox(agent: Agent) -> tuple[Task, TaskMessagesQueue]:
    task = Task(agent_id=agent.agent_id, command="mock_cmd", arguments={})
    agent._tasks_service._register_task(task=task, agent=agent)
    outbox = TaskMessagesQueue(queue_activity_notifier=agent._outbox_activity)
    runtime = TaskRuntime()
    runtime.attach(handler=None, inbox=None, outbox=outbox)
    agent._task_runtime_service.attach_task_runtime(
        task_id=task.task_id,
        agent_id=agent.agent_id,
        task_runtime=runtime,
    )
    return task, outbox


def _input(task: Task, **data) -> TaskInputMessageModel:
    return TaskInputMessageModel(task_id=task.task_id, data=data)


# --- get_next_task_message_by_task_id ---


@pytest.mark.anyio
async def test_get_by_id_returns_message():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    message = _input(task, n=1)
    await outbox.put(message)

    result = await agent.get_next_task_message_by_task_id(
        task_id=task.task_id, timeout=0
    )

    assert result == message


@pytest.mark.anyio
async def test_get_by_id_returns_none_on_timeout():
    # An open but empty outbox is a transient miss: None, distinct from END_OF_STREAM.
    agent = _make_agent()
    task, _ = _add_outbox(agent)

    result = await agent.get_next_task_message_by_task_id(
        task_id=task.task_id, timeout=0
    )

    assert result is None


@pytest.mark.anyio
async def test_get_by_id_returns_end_of_stream_when_exhausted_and_drops_outbox():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    await outbox.shutdown()

    result = await agent.get_next_task_message_by_task_id(
        task_id=task.task_id, timeout=0
    )

    assert result is END_OF_STREAM
    # The exhausted outbox is dropped so subsequent reads keep reporting end of stream.
    assert agent._task_runtime_service.get_task_runtime(task_id=task.task_id) is None
    again = await agent.get_next_task_message_by_task_id(
        task_id=task.task_id, timeout=0
    )
    assert again is END_OF_STREAM


@pytest.mark.anyio
async def test_get_by_id_returns_end_of_stream_for_missing_outbox():
    # A task with no outbox (never produced or already drained) reports end of stream.
    agent = _make_agent()
    task = Task(agent_id=agent.agent_id, command="mock_cmd", arguments={})
    agent._tasks_service._register_task(task=task, agent=agent)

    result = await agent.get_next_task_message_by_task_id(
        task_id=task.task_id, timeout=0
    )

    assert result is END_OF_STREAM


@pytest.mark.anyio
async def test_get_by_id_launch_message_transitions_task_to_running():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    launch = TaskLaunchMessageModel(task_id=task.task_id, command=task.command)
    await outbox.put(launch)
    assert task.status.state == TaskState.QUEUED

    result = await agent.get_next_task_message_by_task_id(
        task_id=task.task_id, timeout=0
    )

    # The QUEUED -> RUNNING transition is driven by an isinstance check on what the
    # outbox returns, so the decode has to hand back a real launch model and not a dict
    # or a message of another type: assert the type explicitly rather than leaving the
    # state transition below as the only thing that would notice.
    assert isinstance(result, TaskLaunchMessageModel)
    assert result == launch
    assert task.status.state == TaskState.RUNNING
    assert task.datetime_started is not None


@pytest.mark.anyio
async def test_drain_by_id_yields_buffered_messages_then_stops():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    first = _input(task, n=1)
    second = _input(task, n=2)
    await outbox.put(first)
    await outbox.put(second)
    await outbox.shutdown()

    collected = [
        message
        async for message in agent.drain_task_messages_by_task_id(task_id=task.task_id)
    ]

    assert collected == [first, second]


# --- get_next_task_message_sequential ---


@pytest.mark.anyio
async def test_get_sequential_returns_message():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    message = _input(task, n=1)
    await outbox.put(message)

    result = await agent.get_next_task_message_sequential(timeout=0)

    assert result == message


@pytest.mark.anyio
async def test_get_sequential_returns_none_on_timeout():
    agent = _make_agent()
    _add_outbox(agent)

    result = await agent.get_next_task_message_sequential(timeout=0)

    assert result is None


@pytest.mark.anyio
async def test_get_sequential_advances_past_exhausted_outbox():
    # The earliest outbox is exhausted; sequential must transparently advance to the next
    # one and never surface END_OF_STREAM to its caller.
    agent = _make_agent()
    first_task, first_outbox = _add_outbox(agent)
    second_task, second_outbox = _add_outbox(agent)
    await first_outbox.shutdown()
    message = _input(second_task, n=1)
    await second_outbox.put(message)

    result = await agent.get_next_task_message_sequential(timeout=None)

    assert result == message
    # The exhausted earliest outbox was dropped as it was passed.
    assert (
        agent._task_runtime_service.get_task_runtime(task_id=first_task.task_id) is None
    )


@pytest.mark.anyio
async def test_get_sequential_polls_past_exhausted_outbox_with_zero_timeout():
    # Regression guard: a zero timeout must still poll (and skip an instantly exhausted
    # earliest outbox), not short-circuit to None before reading anything.
    agent = _make_agent()
    first_task, first_outbox = _add_outbox(agent)
    second_task, second_outbox = _add_outbox(agent)
    await first_outbox.shutdown()
    message = _input(second_task, n=1)
    await second_outbox.put(message)

    result = await agent.get_next_task_message_sequential(timeout=0)

    assert result == message


@pytest.mark.anyio
async def test_sequential_muxer_does_not_scan_retained_terminal_records():
    agent = _make_agent()
    for _ in range(10):
        terminal_task = Task(
            agent_id=agent.agent_id,
            command="mock_cmd",
            arguments={},
        )
        terminal_task.status._transition_to_succeeded()
        terminal_task.datetime_completed = utc_now()
        agent._tasks_service._register_task(task=terminal_task, agent=agent)

    live_task, live_outbox = _add_outbox(agent)
    message = _input(live_task, n=1)
    await live_outbox.put(message)
    original_get_all_tasks = agent._tasks_service.get_all_tasks

    def _fail_if_records_are_scanned(*_args, **_kwargs):
        raise AssertionError("sequential muxer scanned task records")

    agent._tasks_service.get_all_tasks = _fail_if_records_are_scanned
    try:
        result = await agent.get_next_task_message_sequential(timeout=0)
    finally:
        agent._tasks_service.get_all_tasks = original_get_all_tasks

    assert result == message


# --- get_next_task_message_any ---


@pytest.mark.anyio
async def test_get_any_returns_available_message():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    message = _input(task, n=1)
    await outbox.put(message)

    result = await agent.get_next_task_message_any(timeout=0)

    assert result == message


@pytest.mark.anyio
async def test_get_any_returns_none_on_timeout():
    agent = _make_agent()
    _add_outbox(agent)

    result = await agent.get_next_task_message_any(timeout=0)

    assert result is None


@pytest.mark.anyio
async def test_get_any_skips_exhausted_outbox():
    agent = _make_agent()
    _first_task, first_outbox = _add_outbox(agent)
    second_task, second_outbox = _add_outbox(agent)
    await first_outbox.shutdown()
    message = _input(second_task, n=1)
    await second_outbox.put(message)

    result = await agent.get_next_task_message_any(timeout=0)

    assert result == message


# --- drain generators (any / sequential) ---


@pytest.mark.anyio
async def test_drain_any_yields_available_message():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    message = _input(task, n=1)
    await outbox.put(message)

    generator = agent.drain_task_messages_any()
    try:
        first = await asyncio.wait_for(anext(generator), timeout=1)
    finally:
        await generator.aclose()

    assert first == message


@pytest.mark.anyio
async def test_drain_sequential_yields_available_message():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    message = _input(task, n=1)
    await outbox.put(message)

    generator = agent.drain_task_messages_sequential()
    try:
        first = await asyncio.wait_for(anext(generator), timeout=1)
    finally:
        await generator.aclose()

    assert first == message


# --- registry ownership and deletion races ---


def test_agent_registry_getters_are_owner_and_state_scoped():
    task_runtime_service = TaskRuntimeService()
    tasks_service = TasksService(
        events_service=_StubEventsService(),
        task_runtime_service=task_runtime_service,
    )
    first_agent = _make_agent(
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    second_agent = _make_agent(
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    queued_task, _ = _add_outbox(first_agent)
    running_task, _ = _add_outbox(first_agent)
    running_task.status._transition_to_running()
    other_task, _ = _add_outbox(second_agent)

    assert first_agent.get_all_tasks() == [queued_task, running_task]
    assert first_agent.get_all_queued_tasks() == [queued_task]
    assert first_agent.get_all_running_tasks() == [running_task]
    assert (
        first_agent.get_task_by_task_id(task_id=str(queued_task.task_id).upper())
        is queued_task
    )
    with pytest.raises(AgentTaskNotFoundError):
        first_agent.get_task_by_task_id(task_id=other_task.task_id)


@pytest.mark.anyio
async def test_queued_deletion_detaches_runtime_cancels_handler_and_shuts_queues():
    agent = _make_agent()
    task = Task(agent_id=agent.agent_id, command="mock_cmd", arguments={})
    agent._tasks_service._register_task(task=task, agent=agent)
    inbox = TaskMessagesQueue()
    outbox = TaskMessagesQueue(queue_activity_notifier=agent._outbox_activity)
    handler = asyncio.create_task(asyncio.Event().wait())
    runtime = TaskRuntime()
    runtime.attach(handler=handler, inbox=inbox, outbox=outbox)
    agent._task_runtime_service.attach_task_runtime(
        task_id=task.task_id,
        agent_id=agent.agent_id,
        task_runtime=runtime,
    )

    await agent._tasks_service.delete_task_by_task_id(task_id=task.task_id)
    await asyncio.sleep(0)

    assert agent._tasks_service.find_task(task_id=task.task_id) is None
    with pytest.raises(AgentTaskNotFoundError):
        agent.get_task_by_task_id(task_id=task.task_id)
    assert agent._task_runtime_service.get_task_runtime(task_id=task.task_id) is None
    assert handler.cancelled()
    assert await inbox.get(timeout=0) is END_OF_STREAM
    assert await outbox.get(timeout=0) is END_OF_STREAM


@pytest.mark.anyio
async def test_reader_parked_on_deleted_task_wakes_with_end_of_stream():
    agent = _make_agent()
    task, _outbox = _add_outbox(agent)
    reader = asyncio.create_task(
        agent.get_next_task_message_by_task_id(task_id=task.task_id)
    )
    await asyncio.sleep(0)

    await agent._tasks_service.delete_task_by_task_id(task_id=task.task_id)

    assert await asyncio.wait_for(reader, timeout=1) is END_OF_STREAM


@pytest.mark.anyio
async def test_sequential_muxer_advances_when_selected_task_is_deleted():
    agent = _make_agent()
    first_task, _first_outbox = _add_outbox(agent)
    second_task, second_outbox = _add_outbox(agent)
    message = _input(second_task, n=2)
    await second_outbox.put(message)
    reader = asyncio.create_task(agent.get_next_task_message_sequential())
    await asyncio.sleep(0)

    await agent._tasks_service.delete_task_by_task_id(task_id=first_task.task_id)

    assert await asyncio.wait_for(reader, timeout=1) == message


class _PausingTaskMessagesQueue(TaskMessagesQueue):
    def __init__(self, queue_activity_notifier: asyncio.Condition):
        super().__init__(queue_activity_notifier=queue_activity_notifier)
        self.message_dequeued = asyncio.Event()
        self.resume_reader = asyncio.Event()

    async def get(self, timeout: float | None = None):
        message = await super().get(timeout=timeout)
        self.message_dequeued.set()
        await self.resume_reader.wait()
        return message


@pytest.mark.anyio
async def test_message_dequeued_before_deletion_is_not_returned():
    agent = _make_agent()
    task = Task(agent_id=agent.agent_id, command="mock_cmd", arguments={})
    agent._tasks_service._register_task(task=task, agent=agent)
    outbox = _PausingTaskMessagesQueue(queue_activity_notifier=agent._outbox_activity)
    runtime = TaskRuntime()
    runtime.attach(handler=None, inbox=None, outbox=outbox)
    agent._task_runtime_service.attach_task_runtime(
        task_id=task.task_id,
        agent_id=agent.agent_id,
        task_runtime=runtime,
    )
    await outbox.put(_input(task, n=1))
    reader = asyncio.create_task(
        agent.get_next_task_message_by_task_id(task_id=task.task_id)
    )
    await outbox.message_dequeued.wait()

    await agent._tasks_service.delete_task_by_task_id(task_id=task.task_id)
    outbox.resume_reader.set()

    assert await asyncio.wait_for(reader, timeout=1) is END_OF_STREAM


@pytest.mark.anyio
async def test_any_muxer_advances_when_dequeued_task_is_deleted():
    agent = _make_agent()
    first_task = Task(agent_id=agent.agent_id, command="mock_cmd", arguments={})
    agent._tasks_service._register_task(task=first_task, agent=agent)
    first_outbox = _PausingTaskMessagesQueue(
        queue_activity_notifier=agent._outbox_activity
    )
    runtime = TaskRuntime()
    runtime.attach(handler=None, inbox=None, outbox=first_outbox)
    agent._task_runtime_service.attach_task_runtime(
        task_id=first_task.task_id,
        agent_id=agent.agent_id,
        task_runtime=runtime,
    )
    await first_outbox.put(_input(first_task, n=1))
    second_task, second_outbox = _add_outbox(agent)
    second_message = _input(second_task, n=2)
    await second_outbox.put(second_message)
    reader = asyncio.create_task(agent.get_next_task_message_any())
    await first_outbox.message_dequeued.wait()

    await agent._tasks_service.delete_task_by_task_id(task_id=first_task.task_id)
    first_outbox.resume_reader.set()

    assert await asyncio.wait_for(reader, timeout=1) == second_message


@pytest.mark.anyio
async def test_terminal_deletion_discards_buffered_outbox():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    await outbox.put(_input(task, n=1))
    task.status._transition_to_succeeded()
    task.datetime_completed = utc_now()

    await agent._tasks_service.delete_task_by_task_id(task_id=task.task_id)

    assert agent._task_runtime_service.get_task_runtime(task_id=task.task_id) is None
    assert await outbox.get(timeout=0) is END_OF_STREAM


@pytest.mark.anyio
async def test_deletion_rejects_a_running_task_but_allows_every_other_state():
    # RUNNING is the single rejected state, which is what lets queued and terminal
    # deletion share one method: their union is everything else.
    agent = _make_agent()
    running_task, running_outbox = _add_outbox(agent)
    await running_outbox.put(
        TaskLaunchMessageModel(
            task_id=running_task.task_id, command=running_task.command
        )
    )
    await agent.get_next_task_message_by_task_id(
        task_id=running_task.task_id, timeout=0
    )
    assert running_task.status.state == TaskState.RUNNING

    with pytest.raises(TaskNotDeletableError):
        await agent._tasks_service.delete_task_by_task_id(task_id=running_task.task_id)
    assert agent._tasks_service.find_task(task_id=running_task.task_id) is running_task

    queued_task, _ = _add_outbox(agent)
    assert queued_task.status.state == TaskState.QUEUED
    await agent._tasks_service.delete_task_by_task_id(task_id=queued_task.task_id)
    assert agent._tasks_service.find_task(task_id=queued_task.task_id) is None

    running_task.status._transition_to_succeeded()
    running_task.datetime_completed = utc_now()
    await agent._tasks_service.delete_task_by_task_id(task_id=running_task.task_id)
    assert agent._tasks_service.find_task(task_id=running_task.task_id) is None


@pytest.mark.anyio
async def test_output_dispatch_rejects_deleted_wrong_owner_and_non_running_tasks():
    task_runtime_service = TaskRuntimeService()
    tasks_service = TasksService(
        events_service=_StubEventsService(),
        task_runtime_service=task_runtime_service,
    )
    first_agent = _make_agent(
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    second_agent = _make_agent(
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    queued_task, _ = _add_outbox(first_agent)
    other_task, _ = _add_outbox(second_agent)
    other_task.status._transition_to_running()

    assert not await first_agent.dispatch_task_output_message(
        TaskOutputMessageModel(task_id=queued_task.task_id, success=True)
    )
    assert not await first_agent.dispatch_task_output_message(
        TaskOutputMessageModel(task_id=other_task.task_id, success=True)
    )

    await tasks_service.delete_task_by_task_id(task_id=queued_task.task_id)
    assert not await first_agent.dispatch_task_output_message(
        TaskOutputMessageModel(task_id=queued_task.task_id, success=True)
    )


class _RuntimeStartupFailureCapability:
    name = "mock_cmd"
    options = {}
    validating_function = None

    def __init__(self, agent: Agent, task: Task):
        raise RuntimeError("startup failed")


class _DeliberateValidationFailureCapability:
    name = "deliberate_validation_failure"
    options = {}
    constructed = False

    @staticmethod
    def validating_function(_arguments):
        raise OptionValueValidationError(
            message="The resolved arguments are incompatible.",
            detail={"reason": "incompatible"},
        )

    def __init__(self, agent: Agent, task: Task):
        self.__class__.constructed = True


class _UnexpectedValidationErrorCapability:
    name = "unexpected_validation_error"
    options = {}
    constructed = False

    @staticmethod
    def validating_function(_arguments):
        raise RuntimeError("validator crashed")

    def __init__(self, agent: Agent, task: Task):
        self.__class__.constructed = True


@pytest.mark.anyio
async def test_submit_task_does_not_register_capability_lookup_failures():
    agent = _make_agent()
    agent.agent_type = type(
        "AgentType",
        (),
        {"agent_capabilities": {}},
    )()

    with pytest.raises(AgentCapabilityNotFoundError):
        await agent.submit_task(command="missing", arguments={})

    assert agent.get_all_tasks() == []


@pytest.mark.anyio
async def test_submit_task_registers_nothing_when_runtime_startup_fails():
    agent = _make_agent()
    agent.agent_type = type(
        "AgentType",
        (),
        {
            "agent_capabilities": {
                _RuntimeStartupFailureCapability.name: _RuntimeStartupFailureCapability
            }
        },
    )()

    with pytest.raises(RuntimeError, match="startup failed"):
        await agent.submit_task(command="mock_cmd", arguments={})

    assert agent.get_all_tasks() == []
    assert not agent._task_runtime_service.has_readable_outbox_for_agent(
        agent_id=agent.agent_id
    )


@pytest.mark.anyio
async def test_deliberate_capability_validation_failure_registers_nothing():
    # A tasking rejected by the capability's validating function was never queued, so it
    # must leave no task record behind, exactly like the capability lookup failures. The
    # error reaches the caller (and therefore the API, as a 422) instead of being
    # reported through a registered FAILED task.
    agent = _make_agent()
    _DeliberateValidationFailureCapability.constructed = False
    agent.agent_type = type(
        "AgentType",
        (),
        {
            "agent_capabilities": {
                _DeliberateValidationFailureCapability.name: (
                    _DeliberateValidationFailureCapability
                )
            }
        },
    )()

    with pytest.raises(AgentCapabilityValidatingFunctionError) as exc_info:
        await agent.submit_task(
            command=_DeliberateValidationFailureCapability.name,
            arguments={},
        )

    assert _DeliberateValidationFailureCapability.name in exc_info.value.message
    assert "resolved arguments are incompatible" in exc_info.value.message
    assert exc_info.value.detail == {"reason": "incompatible"}
    assert agent.get_all_tasks() == []
    assert not agent._task_runtime_service.has_readable_outbox_for_agent(
        agent_id=agent.agent_id
    )
    assert not _DeliberateValidationFailureCapability.constructed


class _RequiredOptionCapability:
    name = "required_option"
    options = {"target": SingleValueOption(name="target", required=True)}
    validating_function = None
    constructed = False

    def __init__(self, agent: Agent, task: Task):
        self.__class__.constructed = True


@pytest.mark.anyio
async def test_submit_task_rejects_missing_required_option_without_registering():
    # Required options are checked before defaults are filled in, so a required option
    # that was simply omitted is reported as missing rather than being defaulted to None
    # and then failing value validation.
    agent = _make_agent()
    _RequiredOptionCapability.constructed = False
    agent.agent_type = type(
        "AgentType",
        (),
        {
            "agent_capabilities": {
                _RequiredOptionCapability.name: _RequiredOptionCapability
            }
        },
    )()

    with pytest.raises(MissingRequiredAgentCapabilityOptionError) as exc_info:
        await agent.submit_task(command=_RequiredOptionCapability.name, arguments={})

    assert "target" in exc_info.value.message
    assert agent.get_all_tasks() == []
    assert not _RequiredOptionCapability.constructed


@pytest.mark.anyio
async def test_submit_task_does_not_mutate_the_provided_arguments():
    # Defaults are resolved into a copy so a rejected tasking leaves the caller's
    # arguments untouched, and so an accepted task owns its own argument set.
    agent = _make_agent()
    agent.agent_type = type(
        "AgentType",
        (),
        {
            "agent_capabilities": {
                _RequiredOptionCapability.name: _RequiredOptionCapability
            }
        },
    )()

    arguments = {}
    with pytest.raises(MissingRequiredAgentCapabilityOptionError):
        await agent.submit_task(
            command=_RequiredOptionCapability.name,
            arguments=arguments,
        )

    assert arguments == {}


@pytest.mark.anyio
async def test_unexpected_capability_validation_error_propagates():
    agent = _make_agent()
    _UnexpectedValidationErrorCapability.constructed = False
    agent.agent_type = type(
        "AgentType",
        (),
        {
            "agent_capabilities": {
                _UnexpectedValidationErrorCapability.name: (
                    _UnexpectedValidationErrorCapability
                )
            }
        },
    )()

    with pytest.raises(RuntimeError, match="validator crashed"):
        await agent.submit_task(
            command=_UnexpectedValidationErrorCapability.name,
            arguments={},
        )

    assert agent.get_all_tasks() == []
    assert not agent._task_runtime_service.has_readable_outbox_for_agent(
        agent_id=agent.agent_id
    )
    assert not _UnexpectedValidationErrorCapability.constructed


@pytest.mark.anyio
async def test_error_pending_tasks_keeps_records_and_releases_runtime():
    agent = _make_agent()
    task = Task(agent_id=agent.agent_id, command="mock_cmd", arguments={})
    agent._tasks_service._register_task(task=task, agent=agent)
    inbox = TaskMessagesQueue()
    outbox = TaskMessagesQueue(queue_activity_notifier=agent._outbox_activity)
    handler = asyncio.create_task(asyncio.Event().wait())
    runtime = TaskRuntime()
    runtime.attach(handler=handler, inbox=inbox, outbox=outbox)
    agent._task_runtime_service.attach_task_runtime(
        task_id=task.task_id,
        agent_id=agent.agent_id,
        task_runtime=runtime,
    )

    assert agent.error_pending_tasks(error_message="agent removed") == [task]
    await asyncio.sleep(0)

    assert agent.get_errored_task_by_task_id(task_id=task.task_id) is task
    assert task.status.state == TaskState.ERRORED
    assert agent._task_runtime_service.get_task_runtime(task_id=task.task_id) is None
    assert handler.cancelled()
    assert await inbox.get(timeout=0) is END_OF_STREAM
    assert await outbox.get(timeout=0) is END_OF_STREAM


@pytest.mark.anyio
async def test_agent_removal_keeps_records_and_tears_down_all_runtime_states():
    events_service = _StubEventsService()
    task_runtime_service = TaskRuntimeService()
    tasks_service = TasksService(
        events_service=events_service,
        task_runtime_service=task_runtime_service,
    )
    agents_service = AgentsService(
        events_service=events_service,
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    deregistered_agent = _make_agent(
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    deleted_agent = _make_agent(
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    deregistered_agent.to_json = lambda: {}
    deleted_agent.to_json = lambda: {}
    agents_service._agents[str(deregistered_agent.agent_id)] = deregistered_agent
    agents_service._agents[str(deleted_agent.agent_id)] = deleted_agent
    deregistered_task, _ = _add_outbox(deregistered_agent)
    deleted_task, _ = _add_outbox(deleted_agent)
    deregistered_terminal_task, deregistered_terminal_outbox = _add_outbox(
        deregistered_agent
    )
    deleted_terminal_task, deleted_terminal_outbox = _add_outbox(deleted_agent)
    for task, outbox in (
        (deregistered_terminal_task, deregistered_terminal_outbox),
        (deleted_terminal_task, deleted_terminal_outbox),
    ):
        await outbox.put(_input(task, buffered=True))
        task.status._transition_to_succeeded()
        task.datetime_completed = utc_now()

    agents_service.deregister_agent_by_agent_id(agent_id=deregistered_agent.agent_id)
    await agents_service.delete_agent_by_agent_id(agent_id=deleted_agent.agent_id)
    await asyncio.sleep(0)

    for task in (deregistered_task, deleted_task):
        assert tasks_service.find_task(task_id=task.task_id) is task
        assert task.status.state == TaskState.ERRORED
        assert task_runtime_service.get_task_runtime(task_id=task.task_id) is None
    for task, outbox in (
        (deregistered_terminal_task, deregistered_terminal_outbox),
        (deleted_terminal_task, deleted_terminal_outbox),
    ):
        assert tasks_service.find_task(task_id=task.task_id) is task
        assert task.status.state == TaskState.SUCCEEDED
        assert task_runtime_service.get_task_runtime(task_id=task.task_id) is None
        assert await outbox.get(timeout=0) is END_OF_STREAM


@pytest.mark.anyio
async def test_removed_agent_is_not_retained_by_surviving_task_record():
    events_service = _StubEventsService()
    task_runtime_service = TaskRuntimeService()
    tasks_service = TasksService(
        events_service=events_service,
        task_runtime_service=task_runtime_service,
    )
    agents_service = AgentsService(
        events_service=events_service,
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    agent = _make_agent(
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    agent.to_json = lambda: {}
    agents_service._agents[str(agent.agent_id)] = agent
    task, outbox = _add_outbox(agent)
    await outbox.put(_input(task, buffered=True))
    task.status._transition_to_succeeded()
    task.datetime_completed = utc_now()
    agent_reference = weakref.ref(agent)

    agents_service.deregister_agent_by_agent_id(agent_id=agent.agent_id)
    del agent
    del outbox
    await asyncio.sleep(0)
    gc.collect()

    assert tasks_service.find_task(task_id=task.task_id) is task
    assert agent_reference() is None


@pytest.mark.anyio
async def test_terminal_retention_evicts_oldest_record_from_agent_getters():
    task_runtime_service = TaskRuntimeService()
    tasks_service = TasksService(
        events_service=_StubEventsService(),
        task_runtime_service=task_runtime_service,
        max_retained_terminal_tasks=1,
    )
    agent = _make_agent(
        tasks_service=tasks_service,
        task_runtime_service=task_runtime_service,
    )
    oldest_task = Task(agent_id=agent.agent_id, command="mock_cmd", arguments={})
    oldest_task.status._transition_to_succeeded()
    oldest_task.datetime_completed = utc_now()
    oldest_outbox = TaskMessagesQueue(queue_activity_notifier=agent._outbox_activity)
    tasks_service._register_task(task=oldest_task, agent=agent)
    runtime = TaskRuntime()
    runtime.attach(handler=None, inbox=None, outbox=oldest_outbox)
    task_runtime_service.attach_task_runtime(
        task_id=oldest_task.task_id,
        agent_id=agent.agent_id,
        task_runtime=runtime,
    )
    newest_task = Task(agent_id=agent.agent_id, command="mock_cmd", arguments={})
    newest_task.status._transition_to_succeeded()
    newest_task.datetime_completed = utc_now()
    tasks_service._register_task(task=newest_task, agent=agent)
    await asyncio.sleep(0)

    assert tasks_service.find_task(task_id=oldest_task.task_id) is None
    assert agent.get_all_tasks() == [newest_task]
    assert task_runtime_service.get_task_runtime(task_id=oldest_task.task_id) is None
    assert await oldest_outbox.get(timeout=0) is END_OF_STREAM
