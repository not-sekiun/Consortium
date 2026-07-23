import asyncio
import uuid

import pytest

from consortium.framework.agents._task_messages_queue import (
    END_OF_STREAM,
    TaskMessagesQueue,
)
from consortium.framework.agents.agent_message_models import TaskInputMessageModel


def _message() -> TaskInputMessageModel:
    return TaskInputMessageModel(task_id=uuid.uuid4(), data={"k": "v"})


def test_end_of_stream_is_a_unique_sentinel():
    # END_OF_STREAM must be a distinct object, not None or any falsey value, so callers
    # can compare against it by identity without colliding with a real message or a
    # timeout signal.
    assert END_OF_STREAM is not None
    assert END_OF_STREAM is END_OF_STREAM
    assert isinstance(END_OF_STREAM, object)


@pytest.mark.anyio
async def test_get_returns_the_put_message():
    queue = TaskMessagesQueue()
    message = _message()

    await queue.put(message)

    assert await queue.get() is message


@pytest.mark.anyio
async def test_get_returns_end_of_stream_after_shutdown_when_empty():
    queue = TaskMessagesQueue()

    await queue.shutdown()

    assert await queue.get() is END_OF_STREAM


@pytest.mark.anyio
async def test_get_drains_buffered_messages_before_end_of_stream():
    # A graceful shutdown still serves any buffered messages first; end of stream is only
    # reported once the backlog has been fully drained.
    queue = TaskMessagesQueue()
    first = _message()
    second = _message()
    await queue.put(first)
    await queue.put(second)

    await queue.shutdown()

    assert await queue.get() is first
    assert await queue.get() is second
    assert await queue.get() is END_OF_STREAM
    # Terminal: every subsequent read keeps reporting end of stream.
    assert await queue.get() is END_OF_STREAM


@pytest.mark.anyio
async def test_immediate_shutdown_drops_buffered_messages():
    queue = TaskMessagesQueue()
    await queue.put(_message())

    await queue.shutdown(immediate=True)

    assert await queue.get() is END_OF_STREAM


@pytest.mark.anyio
async def test_get_raises_timeout_error_when_open_and_empty():
    # An open (not shut down) empty queue is a transient "nothing yet" condition, which
    # surfaces as TimeoutError, distinct from the END_OF_STREAM terminal signal.
    queue = TaskMessagesQueue()

    with pytest.raises(TimeoutError):
        await queue.get(timeout=0)

    with pytest.raises(TimeoutError):
        await queue.get(timeout=0.01)


@pytest.mark.anyio
async def test_timeout_and_end_of_stream_are_distinct():
    # The crux of the sentinel design: the same empty queue reports a timeout while open
    # and END_OF_STREAM once shut down, so the two are never conflated.
    queue = TaskMessagesQueue()

    with pytest.raises(TimeoutError):
        await queue.get(timeout=0)

    await queue.shutdown()

    assert await queue.get(timeout=0) is END_OF_STREAM


@pytest.mark.anyio
async def test_is_at_end_of_stream_reflects_shutdown_and_drain_state():
    queue = TaskMessagesQueue()
    assert queue.is_at_end_of_stream() is False

    await queue.put(_message())
    await queue.shutdown()
    # Shut down but a buffered message remains, so not yet at end of stream.
    assert queue.is_at_end_of_stream() is False

    await queue.get()
    # Shut down and fully drained.
    assert queue.is_at_end_of_stream() is True


@pytest.mark.anyio
async def test_get_blocks_until_a_message_is_put():
    queue = TaskMessagesQueue()
    message = _message()

    async def _put_after_delay():
        await asyncio.sleep(0.01)
        await queue.put(message)

    getter = asyncio.create_task(queue.get(timeout=None))
    putter = asyncio.create_task(_put_after_delay())

    result = await asyncio.wait_for(getter, timeout=1)
    await putter

    assert result is message


@pytest.mark.anyio
async def test_get_returns_end_of_stream_when_shutdown_while_waiting():
    # A consumer already blocked in get must observe end of stream when the queue is shut
    # down out from under it, not hang forever.
    queue = TaskMessagesQueue()

    async def _shutdown_after_delay():
        await asyncio.sleep(0.01)
        await queue.shutdown()

    getter = asyncio.create_task(queue.get(timeout=None))
    shutter = asyncio.create_task(_shutdown_after_delay())

    result = await asyncio.wait_for(getter, timeout=1)
    await shutter

    assert result is END_OF_STREAM
