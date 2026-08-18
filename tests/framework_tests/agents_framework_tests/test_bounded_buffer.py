import asyncio

import pytest

from consortium.framework.agents._bounded_buffer import END_OF_STREAM, BoundedBuffer

# The primitive stores whatever it is handed and charges whatever the sizing callable
# returns, so these tests use `bytes` entries sized by `len`: the accounting is then a
# plain byte count and a cap can be expressed as the exact number of entries it admits.


def _buffer(maximum_memory_size: int | None = None) -> BoundedBuffer[bytes]:
    return BoundedBuffer(entry_size=len, maximum_memory_size=maximum_memory_size)


def test_a_non_positive_maximum_memory_size_is_rejected():
    # A cap of zero admits nothing but the one-time oversize exception, which would make
    # every put a special case, so it is refused at construction rather than at runtime.
    with pytest.raises(ValueError):
        _buffer(maximum_memory_size=0)

    with pytest.raises(ValueError):
        _buffer(maximum_memory_size=-1)


@pytest.mark.anyio
async def test_entries_come_back_in_the_order_they_were_put():
    buffer = _buffer()

    await buffer.put(b"first")
    await buffer.put(b"second")

    assert await buffer.get() == b"first"
    assert await buffer.get() == b"second"


@pytest.mark.anyio
async def test_entries_are_stored_by_reference():
    # Unlike the message queue, which serializes on the way in, the primitive hands back
    # the object it was given. Anything a subclass needs copied it copies itself.
    buffer = BoundedBuffer(entry_size=lambda entry: 1)
    entry = object()

    await buffer.put(entry)

    assert await buffer.get() is entry


@pytest.mark.anyio
async def test_get_raises_timeout_error_when_open_and_empty():
    # An open (not shut down) empty buffer is a transient "nothing yet" condition, which
    # surfaces as TimeoutError, distinct from the END_OF_STREAM terminal signal.
    buffer = _buffer()

    with pytest.raises(TimeoutError):
        await buffer.get(timeout=0)

    with pytest.raises(TimeoutError):
        await buffer.get(timeout=0.01)


@pytest.mark.anyio
async def test_timeout_and_end_of_stream_are_distinct():
    # The crux of the sentinel design: the same empty buffer reports a timeout while open
    # and END_OF_STREAM once shut down, so the two are never conflated.
    buffer = _buffer()

    with pytest.raises(TimeoutError):
        await buffer.get(timeout=0)

    await buffer.shutdown()

    assert await buffer.get(timeout=0) is END_OF_STREAM


@pytest.mark.anyio
async def test_get_drains_buffered_entries_before_end_of_stream():
    buffer = _buffer()
    await buffer.put(b"first")
    await buffer.put(b"second")

    await buffer.shutdown()

    assert await buffer.get() == b"first"
    assert await buffer.get() == b"second"
    assert await buffer.get() is END_OF_STREAM
    # Terminal: every subsequent read keeps reporting end of stream.
    assert await buffer.get() is END_OF_STREAM


@pytest.mark.anyio
async def test_immediate_shutdown_drops_buffered_entries_and_their_accounting():
    buffer = _buffer(maximum_memory_size=64)
    await buffer.put(b"dropped")

    await buffer.shutdown(immediate=True)

    assert await buffer.get() is END_OF_STREAM
    assert buffer._current_memory_size == 0


@pytest.mark.anyio
async def test_is_at_end_of_stream_reflects_shutdown_and_drain_state():
    buffer = _buffer()
    assert buffer.is_at_end_of_stream() is False

    await buffer.put(b"buffered")
    await buffer.shutdown()
    # Shut down but not yet drained: the backlog is still readable.
    assert buffer.is_at_end_of_stream() is False

    await buffer.get()

    assert buffer.is_at_end_of_stream() is True


@pytest.mark.anyio
async def test_put_after_shutdown_is_an_error_rather_than_a_wait():
    # A full buffer is transient back pressure, a shut down one is terminal, so the two
    # are reported differently: TimeoutError against QueueShutDown.
    buffer = _buffer()
    await buffer.shutdown()

    with pytest.raises(asyncio.QueueShutDown):
        await buffer.put(b"rejected")


@pytest.mark.anyio
async def test_a_parked_put_is_woken_by_a_shutdown():
    buffer = _buffer(maximum_memory_size=4)
    await buffer.put(b"full")
    parked = asyncio.create_task(buffer.put(b"next"))
    await asyncio.sleep(0)
    assert parked.done() is False

    await buffer.shutdown()

    with pytest.raises(asyncio.QueueShutDown):
        await asyncio.wait_for(parked, timeout=1)


@pytest.mark.anyio
async def test_put_applies_back_pressure_until_space_is_freed():
    buffer = _buffer(maximum_memory_size=4)
    await buffer.put(b"full")

    assert buffer.full() is True
    with pytest.raises(TimeoutError):
        await buffer.put(b"next", timeout=0)

    assert await buffer.get() == b"full"
    assert buffer.full() is False
    await buffer.put(b"next", timeout=0)


@pytest.mark.anyio
async def test_a_parked_put_completes_once_a_get_frees_space():
    buffer = _buffer(maximum_memory_size=4)
    await buffer.put(b"full")
    parked = asyncio.create_task(buffer.put(b"next"))
    await asyncio.sleep(0)
    assert parked.done() is False

    assert await buffer.get() == b"full"

    await asyncio.wait_for(parked, timeout=1)
    assert await buffer.get() == b"next"


@pytest.mark.anyio
async def test_an_entry_larger_than_the_buffer_is_admitted_when_empty():
    # The one-time exception: an oversized entry cannot fit anywhere, so an empty buffer
    # takes it rather than blocking its producer forever. It does not extend to the next
    # entry, which waits for the oversized one to be taken off.
    buffer = _buffer(maximum_memory_size=1)

    await buffer.put(b"oversized", timeout=0)

    with pytest.raises(TimeoutError):
        await buffer.put(b"next", timeout=0)
    assert await buffer.get() == b"oversized"


@pytest.mark.anyio
async def test_an_unbounded_buffer_is_never_full():
    buffer = _buffer()

    await buffer.put(b"x" * 4096, timeout=0)

    assert buffer.full() is False


@pytest.mark.anyio
async def test_memory_accounting_returns_to_zero_when_drained():
    buffer = _buffer(maximum_memory_size=64)

    await buffer.put(b"first")
    await buffer.put(b"second")
    assert buffer._current_memory_size == len(b"first") + len(b"second")

    await buffer.get()
    await buffer.get()

    assert buffer._current_memory_size == 0


@pytest.mark.anyio
async def test_the_cap_is_charged_against_the_sizing_callable_not_the_entry():
    # Sizing is the caller's to define: the primitive has no view on what an entry costs,
    # which is what lets the message queue charge a payload it holds by reference.
    buffer = BoundedBuffer(entry_size=lambda entry: 10, maximum_memory_size=10)

    await buffer.put(b"")

    assert buffer._current_memory_size == 10
    assert buffer.full() is True
