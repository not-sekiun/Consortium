import asyncio
import sys
import uuid

import orjson
import pytest

from consortium.framework.agents._task_messages_queue import (
    _MESSAGE_ENTRY_OVERHEAD,
    END_OF_STREAM,
    TaskMessagesQueue,
    _decode_task_message,
    _encode_task_message,
    _task_message_entry_size,
)
from consortium.framework.agents.agent_message_models import (
    Payload,
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)

# The queue holds the wire form of a message, not the model that was put on it, so a
# message that goes through it comes back as an equal instance rather than the same
# object. Every assertion here is on equality for that reason: an identity assertion
# would be asserting the queue does not serialize.


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

    assert await queue.get() == message


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

    assert await queue.get() == first
    assert await queue.get() == second
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

    assert result == message


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


# --- encoding ---


def _launch() -> TaskLaunchMessageModel:
    return TaskLaunchMessageModel(
        task_id=uuid.uuid4(),
        command="list_processes",
        arguments={"filter": "svchost", "limit": 20},
        data={"nested": {"list": [1, 2.5, True, None, "text"]}},
    )


async def _spooled_payload(data: bytes) -> Payload:
    # A payload whose bytes are on disk rather than resident. The zero threshold forces
    # the spill rather than relying on the size of the test data.
    async def _chunks():
        yield data

    return await Payload.from_async_iterable(_chunks(), spool_to_disk_above=1)


def _output() -> TaskOutputMessageModel:
    return TaskOutputMessageModel(
        task_id=uuid.uuid4(),
        success=True,
        message="ok",
        data={"records": [{"pid": index} for index in range(5)]},
    )


@pytest.mark.parametrize("message_factory", [_launch, _message, _output])
def test_encode_decode_round_trip_is_faithful(message_factory):
    message = message_factory()

    decoded = _decode_task_message(_encode_task_message(message), type(message))

    assert type(decoded) is type(message)
    assert decoded == message
    assert decoded.payload is None


@pytest.mark.parametrize("message_factory", [_launch, _message, _output])
def test_pydantic_and_orjson_encodings_are_byte_identical(message_factory):
    # The encoder falls back from orjson to pydantic on integers orjson cannot
    # represent, which is only safe as an invisible substitution because the two agree
    # byte for byte on everything else. If they ever diverge the queue has two output
    # dialects and the fallback stops being an implementation detail.
    message = message_factory()

    assert (
        orjson.dumps(message.to_json())
        == message.model_dump_json(exclude={"payload"}).encode()
    )


def test_encoder_falls_back_for_integers_beyond_64_bits():
    # A 160 bit certificate serial: `data` is a dict[str, JsonValue] so this validates
    # into the model exactly, and orjson refuses to encode it, which is what the
    # fallback exists for. The value has to survive the round trip bit for bit: it is an
    # identifier that gets compared and looked up, so an approximation is the wrong one.
    serial = 4324402459395946597462245728957861835611784311
    message = TaskOutputMessageModel(
        task_id=uuid.uuid4(), success=True, data={"serial": serial}
    )

    with pytest.raises(TypeError):
        orjson.dumps(message.to_json())

    decoded = _decode_task_message(
        _encode_task_message(message), TaskOutputMessageModel
    )

    assert decoded.data["serial"] == serial


def test_decode_never_uses_orjson_loads(monkeypatch):
    # Guard against reintroducing orjson on the decode path. It does not raise on
    # integers beyond 64 bits the way encoding does: it silently degrades them to float,
    # so the failure would be a corrupted identifier that still looks plausible rather
    # than an error anybody notices. Decoding is pydantic's job and this fails loudly if
    # that changes.
    def _fail(*args, **kwargs):
        raise AssertionError("orjson.loads must not be used to decode a task message")

    monkeypatch.setattr(orjson, "loads", _fail)
    message = _output()

    assert (
        _decode_task_message(_encode_task_message(message), TaskOutputMessageModel)
        == message
    )


@pytest.mark.anyio
async def test_get_returns_each_message_as_the_type_it_was_put_as():
    # A single queue carries more than one message type (an outbox holds launches and
    # inputs), and the types overlap: an output blob validates as an input message,
    # since extra keys are ignored and every field but task_id has a default. Deciding
    # from the blob would be guessing, so the type is recorded per message and this
    # asserts the queue hands back what it was given. The launch case matters beyond the
    # type: the QUEUED -> RUNNING transition is an isinstance check on what it returns.
    queue = TaskMessagesQueue()
    for message in (_launch(), _message(), _output()):
        await queue.put(message)
        assert type(await queue.get()) is type(message)


@pytest.mark.anyio
async def test_payloads_are_carried_by_reference_and_never_serialized():
    # A payload's bytes stay out of the blob and the payload is carried by reference, so
    # the same object comes back out and is still readable, however it is backed. The
    # spooled case is the one that matters: its bytes are in a temporary file whose
    # lifetime is the payload's, so serializing a copy would be both wasteful and wrong.
    queue = TaskMessagesQueue()
    in_memory = Payload.from_bytes(b"resident")
    spooled = await _spooled_payload(b"spilled to disk")
    await queue.put(TaskInputMessageModel(task_id=uuid.uuid4(), payload=in_memory))
    await queue.put(TaskInputMessageModel(task_id=uuid.uuid4(), payload=spooled))

    resident_message = await queue.get()
    spooled_message = await queue.get()

    assert resident_message.payload is in_memory
    assert await resident_message.payload.read() == b"resident"
    assert spooled_message.payload is spooled
    assert await spooled_message.payload.read() == b"spilled to disk"


@pytest.mark.anyio
async def test_a_validated_message_is_the_only_way_onto_the_queue():
    # Encoding is internal to `put`. There is deliberately no route that takes bytes: it
    # would save an encode and give up the guarantee that everything queued is a message
    # the models accepted.
    queue = TaskMessagesQueue()

    assert not hasattr(queue, "put_encoded")
    with pytest.raises(AttributeError):
        await queue.put(_encode_task_message(_output()))


# --- sizing ---


def test_message_entry_overhead_matches_this_interpreter():
    # The constant is two CPython object header sizes, which move between versions. If
    # this fails on a new Python the accounting is not wrong by much, but re-derive it
    # with tools/message_sizing_benchmark.py rather than adjusting it by hand.
    json_blob = b"{}"
    entry = (json_blob, None, TaskOutputMessageModel)

    assert _MESSAGE_ENTRY_OVERHEAD == (sys.getsizeof(json_blob) - len(json_blob)) + (
        sys.getsizeof(entry)
    )


def test_entry_size_is_exact_against_getsizeof_composition():
    # Sizing is an accounting fact, not an estimate: what the queue charges is exactly
    # what the objects it holds occupy. The recorded type is a shared class object, so
    # only the tuple slot pointing at it is anybody's to charge.
    json_blob = _encode_task_message(_output())
    entry = (json_blob, None, TaskOutputMessageModel)

    assert _task_message_entry_size(json_blob, None) == sys.getsizeof(
        json_blob
    ) + sys.getsizeof(entry)


@pytest.mark.anyio
async def test_entry_size_counts_resident_payload_bytes_but_not_spooled_ones():
    json_blob = _encode_task_message(_message())
    in_memory = Payload.from_bytes(b"x" * 1000)
    spooled = await _spooled_payload(b"y" * 1000)

    # A payload held in memory is charged in full: those bytes are resident whether the
    # queue counts them or not.
    assert (
        _task_message_entry_size(json_blob, in_memory)
        == _task_message_entry_size(json_blob, None) + sys.getsizeof(in_memory) + 1000
    )
    # One spilled to disk holds nothing in memory, so only the wrapper is charged. This
    # is what lets the payload cap exceed a queue's memory budget.
    assert spooled._resident_size == 0
    assert _task_message_entry_size(json_blob, spooled) == _task_message_entry_size(
        json_blob, None
    ) + sys.getsizeof(spooled)


@pytest.mark.anyio
async def test_memory_accounting_returns_to_zero_when_drained():
    queue = TaskMessagesQueue(maximum_memory_size=1024 * 1024)
    await queue.put(_message())
    await queue.put(_output())

    assert queue._current_memory_size > 0

    await queue.get()
    await queue.get()

    assert queue._current_memory_size == 0


@pytest.mark.anyio
async def test_put_applies_back_pressure_until_space_is_freed():
    message = _message()
    # Sized to hold exactly one message so the second put has to wait for the first to
    # be taken off.
    queue = TaskMessagesQueue(
        maximum_memory_size=_task_message_entry_size(
            _encode_task_message(message), None
        )
    )
    await queue.put(message)

    assert queue.full() is True
    with pytest.raises(TimeoutError):
        await queue.put(_message(), timeout=0)

    assert await queue.get() == message
    assert queue.full() is False
    # Space was freed, so the same put now goes through.
    await queue.put(_message(), timeout=0)


@pytest.mark.anyio
async def test_a_message_larger_than_the_queue_is_admitted_when_empty():
    # The one-time exception: an oversized message cannot fit anywhere, so an empty
    # queue takes it rather than blocking its producer forever.
    queue = TaskMessagesQueue(maximum_memory_size=1)
    message = _output()

    await queue.put(message, timeout=0)

    assert await queue.get() == message
