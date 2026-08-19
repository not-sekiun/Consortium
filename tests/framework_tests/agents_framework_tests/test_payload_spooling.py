import io
from collections.abc import AsyncIterator

import pytest

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    PayloadTooLargeError,
)
from consortium.framework.agents import _resource_limits
from consortium.framework.agents._resource_limits import (
    QUEUE_MEMORY_LIMIT,
    SPOOL_TO_DISK_ABOVE,
    validate_size_limits,
)
from consortium.framework.agents.agent_message_models import Payload

# Where a payload's bytes live is deliberately invisible on the read path, so these tests
# reach for the private `_resident_size` to assert it: it is the only observable
# difference between a resident payload and a spilled one, and it is what the queue's
# memory accounting charges against. Asserting on it is asserting the spill happened.


def _content(size: int) -> bytes:
    # Non-uniform on purpose so a truncated or misordered copy is visible in a comparison
    # rather than passing against an equally sized run of the same byte.
    return (b"consortium-payload-" * ((size // 19) + 1))[:size]


async def _source(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


async def _counting_source(
    chunks: list[bytes],
    consumed: list[bytes],
) -> AsyncIterator[bytes]:
    for chunk in chunks:
        consumed.append(chunk)
        yield chunk


# --- The framework's default limits ---------------------------------------------------


def test_spill_threshold_is_an_eighth_of_the_queue_limit():
    # The ratio is load bearing rather than incidental: it is what lets eight
    # max-resident payloads coexist in one queue before a producer is back-pressured.
    # Retuning one of the two without the other changes how much can be in flight.
    assert SPOOL_TO_DISK_ABOVE == 512 * 1024
    assert QUEUE_MEMORY_LIMIT == 4 * 1024 * 1024
    assert SPOOL_TO_DISK_ABOVE * 8 == QUEUE_MEMORY_LIMIT


def test_framework_declares_no_payload_size_cap():
    # A framework wide payload cap is policy, and policy belongs to the transport that
    # can attribute and enforce it. This pins that decision: reintroducing a module level
    # cap here would silently bound every transport again.
    assert not hasattr(_resource_limits, "MAX_PAYLOAD_SIZE")


def test_validate_size_limits_accepts_the_shipped_defaults():
    validate_size_limits()


def test_validate_size_limits_rejects_a_threshold_at_or_above_the_queue_limit():
    # At or above the limit a single resident payload cannot fit in a queue's budget, so
    # the queue admits it only through its one-time oversize exception and then blocks.
    # Failing here turns that deadlock into an error at construction time.
    with pytest.raises(ValueError):
        validate_size_limits(queue_memory_limit=1024, spool_to_disk_above=1024)
    with pytest.raises(ValueError):
        validate_size_limits(queue_memory_limit=1024, spool_to_disk_above=2048)


def test_validate_size_limits_takes_no_payload_cap():
    # The removed invariant tied the spill threshold to a payload cap that nothing
    # enforced, which made an otherwise legitimate retune fail at import.
    with pytest.raises(TypeError):
        validate_size_limits(max_payload_size=1024)


# --- The default spill boundary -------------------------------------------------------


@pytest.mark.anyio
async def test_payload_at_the_default_threshold_stays_resident():
    data = _content(SPOOL_TO_DISK_ABOVE)

    payload = await Payload.from_async_iterable(_source(data))

    assert payload.size == SPOOL_TO_DISK_ABOVE
    assert payload._resident_size == SPOOL_TO_DISK_ABOVE


@pytest.mark.anyio
async def test_payload_one_byte_over_the_default_threshold_spills_to_disk():
    data = _content(SPOOL_TO_DISK_ABOVE + 1)

    payload = await Payload.from_async_iterable(_source(data))

    assert payload.size == SPOOL_TO_DISK_ABOVE + 1
    # Zero, not merely smaller: a spilled payload costs a queue no memory at all.
    assert payload._resident_size == 0


@pytest.mark.anyio
async def test_the_threshold_applies_to_the_total_not_to_a_single_chunk():
    # Chunk size is the transport's business. Spilling is decided by what the payload
    # adds up to, so a stream of small chunks still rolls once their total crosses.
    chunk = _content(1024)
    chunks = [chunk] * ((SPOOL_TO_DISK_ABOVE // 1024) + 1)

    payload = await Payload.from_async_iterable(_source(*chunks))

    assert payload.size == len(chunk) * len(chunks)
    assert payload._resident_size == 0


@pytest.mark.anyio
async def test_a_spilled_payload_reads_back_exactly_what_it_was_given():
    data = _content(SPOOL_TO_DISK_ABOVE * 2)

    payload = await Payload.from_async_iterable(_source(data))

    assert await payload.read() == data


@pytest.mark.anyio
async def test_a_spilled_payload_is_re_readable():
    # Spilling must be invisible to readers, including that reading does not consume: a
    # payload is read and streamed any number of times whichever side of the threshold
    # it landed on.
    data = _content(SPOOL_TO_DISK_ABOVE + 1)
    payload = await Payload.from_async_iterable(_source(data))

    assert await payload.read() == data
    assert await payload.read() == data
    assert b"".join([chunk async for chunk in payload]) == data
    assert b"".join([chunk async for chunk in payload]) == data


@pytest.mark.anyio
async def test_streaming_and_reading_agree_across_the_threshold():
    resident = await Payload.from_async_iterable(_source(_content(1024)))
    spilled = await Payload.from_async_iterable(
        _source(_content(SPOOL_TO_DISK_ABOVE + 1))
    )

    for payload in (resident, spilled):
        assert b"".join([chunk async for chunk in payload]) == await payload.read()


# --- The size cap is opt in -----------------------------------------------------------


@pytest.mark.anyio
async def test_receiving_is_uncapped_by_default():
    # No caller passing `max_size` means no limit, so a payload far past any size the
    # framework once defaulted to is accepted. This is the behaviour a transport opts out
    # of, not one it opts into.
    data = _content(SPOOL_TO_DISK_ABOVE * 4)

    payload = await Payload.from_async_iterable(_source(data))

    assert payload.size == len(data)


@pytest.mark.anyio
async def test_an_explicit_cap_rejects_an_oversized_payload():
    with pytest.raises(PayloadTooLargeError) as excinfo:
        await Payload.from_async_iterable(_source(_content(2048)), max_size=1024)

    # The cap is reported so a transport can tell an agent what it may resend within.
    assert excinfo.value.detail == {"max_size": 1024}


@pytest.mark.anyio
async def test_an_explicit_cap_admits_a_payload_of_exactly_the_cap():
    payload = await Payload.from_async_iterable(_source(_content(1024)), max_size=1024)

    assert payload.size == 1024


@pytest.mark.anyio
async def test_an_explicit_cap_is_enforced_mid_stream():
    # The point of enforcing as bytes arrive is that an unbounded upload is refused
    # without being buffered first, so the source must be abandoned rather than drained.
    chunks = [_content(512)] * 100
    consumed: list[bytes] = []

    with pytest.raises(PayloadTooLargeError):
        await Payload.from_async_iterable(
            _counting_source(chunks, consumed), max_size=1024
        )

    assert len(consumed) < len(chunks)


# --- from_file copies rather than referencing -----------------------------------------


@pytest.mark.anyio
async def test_from_file_survives_the_source_being_deleted(tmp_path):
    # The behaviour the copy exists for. A queued message may not be consumed for days,
    # and unlinking here also asserts the payload holds no descriptor on the file, which
    # on Windows would block the delete outright.
    source = tmp_path / "implant.bin"
    data = _content(4096)
    source.write_bytes(data)

    payload = await Payload.from_file(source)
    source.unlink()

    assert not source.exists()
    assert await payload.read() == data


@pytest.mark.anyio
async def test_from_file_snapshots_the_contents_at_construction(tmp_path):
    # Existence is not the only thing that can change between queueing and consumption.
    # A payload records the file an operator chose, not whatever later sits at the path.
    source = tmp_path / "notes.txt"
    source.write_bytes(b"original")

    payload = await Payload.from_file(source)
    source.write_bytes(b"replaced after the fact")

    assert await payload.read() == b"original"


@pytest.mark.anyio
async def test_from_file_leaves_the_source_writable_immediately(tmp_path):
    source = tmp_path / "held.bin"
    source.write_bytes(_content(SPOOL_TO_DISK_ABOVE * 2))

    payload = await Payload.from_file(source)

    # Opening for write would fail on Windows if the payload still held the file open.
    with open(source, "wb") as handle:
        handle.write(b"rewritten")
    assert payload.size == SPOOL_TO_DISK_ABOVE * 2


@pytest.mark.anyio
async def test_from_file_spills_on_the_same_default_threshold(tmp_path):
    small = tmp_path / "small.bin"
    small.write_bytes(_content(SPOOL_TO_DISK_ABOVE))
    large = tmp_path / "large.bin"
    large.write_bytes(_content(SPOOL_TO_DISK_ABOVE + 1))

    assert (await Payload.from_file(small))._resident_size == SPOOL_TO_DISK_ABOVE
    assert (await Payload.from_file(large))._resident_size == 0


@pytest.mark.anyio
async def test_from_file_defaults_the_filename_to_the_files_name(tmp_path):
    source = tmp_path / "loader.exe"
    source.write_bytes(b"data")

    payload = await Payload.from_file(source)

    assert payload.filename == "loader.exe"
    # Not inferred from the extension: a confidently wrong content type is worse than
    # none, so it stays the caller's to declare.
    assert payload.content_type is None


@pytest.mark.anyio
async def test_from_file_prefers_an_explicit_filename(tmp_path):
    source = tmp_path / "tmp_upload_1234"
    source.write_bytes(b"data")

    payload = await Payload.from_file(source, filename="report.pdf")

    assert payload.filename == "report.pdf"


@pytest.mark.anyio
async def test_from_file_accepts_a_path_as_a_string(tmp_path):
    source = tmp_path / "as_str.bin"
    source.write_bytes(b"data")

    payload = await Payload.from_file(str(source))

    assert payload.filename == "as_str.bin"
    assert await payload.read() == b"data"


@pytest.mark.anyio
async def test_from_file_is_uncapped_by_default_and_honours_an_explicit_cap(tmp_path):
    source = tmp_path / "big.bin"
    source.write_bytes(_content(4096))

    assert (await Payload.from_file(source)).size == 4096
    with pytest.raises(PayloadTooLargeError):
        await Payload.from_file(source, max_size=1024)


@pytest.mark.anyio
async def test_from_file_raises_the_underlying_os_error(tmp_path):
    # Left unwrapped: the caller supplied the path, so the OS error already says what a
    # framework exception would have to restate.
    with pytest.raises(OSError):
        await Payload.from_file(tmp_path / "missing.bin")
    with pytest.raises(OSError):
        await Payload.from_file(tmp_path)


# --- from_file_like copies rather than referencing ------------------------------------


@pytest.mark.anyio
async def test_from_file_like_copies_out_of_the_object():
    fileobj = io.BytesIO(_content(4096))

    payload = await Payload.from_file_like(fileobj)
    fileobj.close()

    assert await payload.read() == _content(4096)


@pytest.mark.anyio
async def test_from_file_like_reads_from_the_current_position():
    # Not rewound: a caller that has already consumed a header is handing over the rest
    # deliberately, and seeking to zero for them would silently put it back.
    fileobj = io.BytesIO(b"headerBODY")
    fileobj.read(6)

    payload = await Payload.from_file_like(fileobj)

    assert await payload.read() == b"BODY"


@pytest.mark.anyio
async def test_from_file_like_does_not_close_the_object():
    fileobj = io.BytesIO(b"data")

    await Payload.from_file_like(fileobj)

    assert not fileobj.closed


@pytest.mark.anyio
async def test_from_file_like_spills_on_the_same_default_threshold():
    resident = await Payload.from_file_like(io.BytesIO(_content(SPOOL_TO_DISK_ABOVE)))
    spilled = await Payload.from_file_like(
        io.BytesIO(_content(SPOOL_TO_DISK_ABOVE + 1))
    )

    assert resident._resident_size == SPOOL_TO_DISK_ABOVE
    assert spilled._resident_size == 0


@pytest.mark.anyio
async def test_from_file_like_is_uncapped_by_default_and_honours_an_explicit_cap():
    assert (await Payload.from_file_like(io.BytesIO(_content(4096)))).size == 4096
    with pytest.raises(PayloadTooLargeError):
        await Payload.from_file_like(io.BytesIO(_content(4096)), max_size=1024)


@pytest.mark.anyio
async def test_from_file_like_carries_no_filename_by_default():
    # Unlike a path, an open object has no name worth trusting, so nothing is inferred.
    payload = await Payload.from_file_like(io.BytesIO(b"data"))

    assert payload.filename is None
    assert payload.content_type is None


# --- Every constructor agrees on the same storage rules -------------------------------


def test_from_bytes_is_always_resident():
    # from_bytes takes bytes the caller already holds, so there is nothing to spill: the
    # payload cannot cost less memory than the argument it was handed.
    payload = Payload.from_bytes(_content(SPOOL_TO_DISK_ABOVE * 2))

    assert payload._resident_size == payload.size


@pytest.mark.anyio
async def test_every_constructor_produces_the_same_payload_for_the_same_bytes(tmp_path):
    data = _content(SPOOL_TO_DISK_ABOVE + 1)
    source = tmp_path / "same.bin"
    source.write_bytes(data)

    payloads = [
        Payload.from_bytes(data),
        await Payload.from_async_iterable(_source(data)),
        await Payload.from_file(source),
        await Payload.from_file_like(io.BytesIO(data)),
    ]

    for payload in payloads:
        assert payload.size == len(data)
        assert await payload.read() == data
