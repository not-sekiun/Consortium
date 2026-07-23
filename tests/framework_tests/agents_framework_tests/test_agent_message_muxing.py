import asyncio

import pytest

from consortium.framework.agents._task_messages_queue import (
    END_OF_STREAM,
    TaskMessagesQueue,
)
from consortium.framework.agents.agent_message_models import (
    TaskInputMessageModel,
    TaskLaunchMessageModel,
)
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.agent_task_objects import AgentTask, AgentTaskState


def _make_agent() -> Agent:
    # The task message routing methods only touch the task/outbox bookkeeping attributes,
    # not the listener, payload or agent type resolution that Agent.__init__ performs
    # (which needs a fully configured server). Build a bare instance and wire up just
    # those attributes so the muxing logic can be exercised in isolation.
    agent = Agent.__new__(Agent)
    agent._tasks = {}
    agent._task_inboxes = {}
    agent._task_outboxes = {}
    agent._outbox_activity = asyncio.Condition()
    agent._new_task_started_event = asyncio.Event()
    return agent


def _add_outbox(agent: Agent) -> tuple[AgentTask, TaskMessagesQueue]:
    task = AgentTask(command="mock_cmd", arguments={})
    agent._tasks[str(task.task_id)] = task
    outbox = TaskMessagesQueue(agent=agent)
    agent._task_outboxes[str(task.task_id)] = outbox
    return task, outbox


def _input(task: AgentTask, **data) -> TaskInputMessageModel:
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

    assert result is message


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
    assert str(task.task_id) not in agent._task_outboxes
    again = await agent.get_next_task_message_by_task_id(
        task_id=task.task_id, timeout=0
    )
    assert again is END_OF_STREAM


@pytest.mark.anyio
async def test_get_by_id_returns_end_of_stream_for_missing_outbox():
    # A task with no outbox (never produced or already drained) reports end of stream.
    agent = _make_agent()
    task = AgentTask(command="mock_cmd", arguments={})
    agent._tasks[str(task.task_id)] = task

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
    assert task.status.state == AgentTaskState.QUEUED

    result = await agent.get_next_task_message_by_task_id(
        task_id=task.task_id, timeout=0
    )

    assert result is launch
    assert task.status.state == AgentTaskState.RUNNING
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

    assert result is message


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

    assert result is message
    # The exhausted earliest outbox was dropped as it was passed.
    assert str(first_task.task_id) not in agent._task_outboxes


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

    assert result is message


# --- get_next_task_message_any ---


@pytest.mark.anyio
async def test_get_any_returns_available_message():
    agent = _make_agent()
    task, outbox = _add_outbox(agent)
    message = _input(task, n=1)
    await outbox.put(message)

    result = await agent.get_next_task_message_any(timeout=0)

    assert result is message


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

    assert result is message


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

    assert first is message


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

    assert first is message
