import asyncio
import sys

import pytest

from consortium.framework.agents._bounded_buffer import END_OF_STREAM
from consortium.framework.agents._channel_buffer import ChannelBuffer


@pytest.mark.anyio
async def test_chunks_come_back_whole_and_in_order():
    # The buffer carries bytes, not a stream: chunk boundaries are preserved exactly as
    # the producer wrote them and nothing is coalesced or split.
    buffer = ChannelBuffer()

    await buffer.put(b"first")
    await buffer.put(b"second")

    assert await buffer.get() == b"first"
    assert await buffer.get() == b"second"


@pytest.mark.anyio
async def test_a_bytearray_is_copied_rather_than_buffered_by_reference():
    buffer = ChannelBuffer()
    chunk = bytearray(b"original")

    await buffer.put(chunk)
    chunk[:] = b"mutated!"

    assert await buffer.get() == b"original"


@pytest.mark.anyio
async def test_an_empty_chunk_is_not_an_end_of_stream_signal():
    # End of stream is the sentinel, never a zero length read, so an empty chunk is
    # carried through like any other.
    buffer = ChannelBuffer()

    await buffer.put(b"")

    assert await buffer.get() == b""


@pytest.mark.anyio
async def test_memory_accounting_charges_the_resident_size_of_each_chunk():
    buffer = ChannelBuffer(maximum_memory_size=4096)
    chunk = b"x" * 64

    await buffer.put(chunk)
    assert buffer._current_memory_size == sys.getsizeof(chunk)

    await buffer.get()

    assert buffer._current_memory_size == 0


@pytest.mark.anyio
async def test_a_full_channel_blocks_its_producer():
    # Phase 0 delivery is RELIABLE only: a producer with no draining consumer waits
    # rather than dropping. Eviction arrives with the `delivery` declaration.
    buffer = ChannelBuffer(maximum_memory_size=sys.getsizeof(b"x" * 64))
    await buffer.put(b"x" * 64)

    parked = asyncio.create_task(buffer.put(b"y" * 64))
    await asyncio.sleep(0)
    assert parked.done() is False

    assert await buffer.get() == b"x" * 64

    await asyncio.wait_for(parked, timeout=1)
    assert await buffer.get() == b"y" * 64


@pytest.mark.anyio
async def test_shutdown_releases_a_consumer_waiting_on_the_channel():
    # How a pump parked on the channel learns the capability has finished.
    buffer = ChannelBuffer()
    reader = asyncio.create_task(buffer.get())
    await asyncio.sleep(0)

    await buffer.shutdown()

    assert await asyncio.wait_for(reader, timeout=1) is END_OF_STREAM
