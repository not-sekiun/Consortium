import asyncio
import uuid
from types import SimpleNamespace

import pytest

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCommunicationEndOfStreamError,
)
from consortium.framework.agents._agent_communicator import _AgentCommunicator
from consortium.framework.agents.agent_message_models import TaskOutputMessageModel


def _make_communicator() -> tuple[_AgentCommunicator, SimpleNamespace, SimpleNamespace]:
    # _AgentCommunicator only uses the agent for its outbox activity condition and to
    # describe itself in the end of stream error, and the task for its identity, so a
    # lightweight stand-in for each is enough to exercise the receive path.
    agent = SimpleNamespace(
        agent_id=uuid.uuid4(),
        name="test-agent",
        _outbox_activity=asyncio.Condition(),
    )
    task = SimpleNamespace(task_id=uuid.uuid4(), command="mock_cmd")
    return _AgentCommunicator(agent=agent, task=task), agent, task


def _output_message(task_id: uuid.UUID) -> TaskOutputMessageModel:
    return TaskOutputMessageModel(task_id=task_id, success=True, message="ok")


@pytest.mark.anyio
async def test_recv_returns_message_from_inbox():
    communicator, _, task = _make_communicator()
    message = _output_message(task.task_id)
    await communicator._task_messages_inbox.put(message)

    assert await communicator.recv_from_agent() is message


@pytest.mark.anyio
async def test_recv_raises_on_end_of_stream():
    # A communicator is coordinated with the remote endpoint, so reaching end of stream is
    # a genuine error rather than a normal termination signal.
    communicator, _, task = _make_communicator()
    await communicator._task_messages_inbox.shutdown()

    with pytest.raises(AgentCommunicationEndOfStreamError) as exc_info:
        await communicator.recv_from_agent()

    # The error references the task it was waiting on.
    message = str(exc_info.value)
    assert task.command in message
    assert str(task.task_id) in message


@pytest.mark.anyio
async def test_recv_propagates_timeout_error():
    # A timeout is a transient miss and must surface as TimeoutError, never as the end of
    # stream error.
    communicator, _, _ = _make_communicator()

    with pytest.raises(TimeoutError):
        await communicator.recv_from_agent(timeout=0)


@pytest.mark.anyio
async def test_recv_drains_buffered_message_before_raising():
    communicator, _, task = _make_communicator()
    message = _output_message(task.task_id)
    await communicator._task_messages_inbox.put(message)
    await communicator._task_messages_inbox.shutdown()

    # The buffered message is served first.
    assert await communicator.recv_from_agent() is message
    # Only once drained does end of stream raise.
    with pytest.raises(AgentCommunicationEndOfStreamError):
        await communicator.recv_from_agent()


@pytest.mark.anyio
async def test_send_and_recv_raises_on_end_of_stream():
    # The send half succeeds (it writes to the outbox) but the coordinated receive half
    # hits end of stream, which must raise.
    communicator, _, _ = _make_communicator()
    await communicator._task_messages_inbox.shutdown()

    with pytest.raises(AgentCommunicationEndOfStreamError):
        await communicator.send_and_recv_from_agent(data={"k": "v"})
