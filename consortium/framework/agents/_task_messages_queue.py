import asyncio
import sys

import orjson

from consortium.framework.agents._bounded_buffer import END_OF_STREAM, BoundedBuffer
from consortium.framework.agents.agent_message_models import (
    Payload,
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)

TaskMessage = TaskLaunchMessageModel | TaskInputMessageModel | TaskOutputMessageModel

# An entry is the wire form of a message, the payload kept out of it, and the type it
# was put as. The payload can wrap a live async stream, so it is carried by reference
# rather than serialized. The type is recorded rather than inferred on the way out: a
# blob does not say what it is, and the models overlap enough that deciding from its
# contents means guessing (every field but task_id has a default and extra keys are
# ignored, so an output message validates as an input message too). The producer knows,
# so it is written down. Costs one shared class pointer per entry.
_QueueEntry = tuple[bytes, Payload | None, type[TaskMessage]]

# What a queued message costs on top of the bytes it carries: the `bytes` object header
# for the encoded blob (33) plus the 3-tuple that holds the blob, its payload and its
# type (72). The type is a shared class object, so only the tuple slot pointing at it is
# charged. Both are CPython object header sizes rather than anything about the message,
# so they move between interpreter versions: re-derive this with
# tools/message_sizing_benchmark.py after a Python upgrade rather than assuming it holds.
_MESSAGE_ENTRY_OVERHEAD = 105


def _encode_task_message(task_message: TaskMessage) -> bytes:
    # Serialize a message to the JSON the queue stores in place of the model. The payload
    # is left out because it can wrap a live async stream, which must not be buffered to
    # be measured or moved.
    try:
        return orjson.dumps(task_message.to_json())
    except TypeError:
        # orjson raises on integers outside the 64-bit range, and its `default=` hook is
        # not consulted for `int` (a natively supported type) so the hook cannot cover
        # them. Fallback to Pydantic's serializer.
        return task_message.model_dump_json(exclude={"payload"}).encode()


def _decode_task_message(
    json_blob: bytes,
    message_type: type[TaskMessage],
    payload: Payload | None = None,
) -> TaskMessage:
    # do not use orjson, it will parse integers greater than 64 bits as floats losing
    # precision. Pydantic parses them exactly, and goes from bytes to model entirely in
    # Rust, so it is also around twice as fast as orjson.loads plus model construction.
    task_message = message_type.model_validate_json(json_blob)
    task_message.payload = payload
    return task_message


def _task_message_entry_size(json_blob: bytes, payload: Payload | None) -> int:
    # What one entry occupies, which is what the queue charges against its cap. This is
    # an accounting fact rather than an estimate: every term is exact and O(1).
    size = len(json_blob) + _MESSAGE_ENTRY_OVERHEAD
    if payload is not None:
        # Only the bytes a payload holds in memory count. Payloads spooled to disk
        # hold no bytes in memory.
        size += sys.getsizeof(payload) + payload._resident_size
    return size


def _queue_entry_size(entry: _QueueEntry) -> int:
    # Adapts the stored entry to the sizing the buffer charges against its cap.
    json_blob, payload, _ = entry
    return _task_message_entry_size(json_blob, payload)


class TaskMessagesQueue[T: TaskMessage](BoundedBuffer[_QueueEntry]):
    def __init__(
        self,
        maximum_memory_size: int | None = None,
        queue_activity_notifier: asyncio.Condition | None = None,
    ):
        super().__init__(
            entry_size=_queue_entry_size,
            maximum_memory_size=maximum_memory_size,
        )
        # When set (the outbox queues are constructed with the owning agent's shared
        # outbox activity condition), every successful put also signals it. That
        # lets Agent.get_next_task_message_any wait across all of an agent's capability
        # outboxes at once and wake as soon as any of them receives a message. Left None
        # for queues that do not participate in that fan-in (for example the inbox).
        self._queue_activity_notifier = queue_activity_notifier

    async def put(
        self,
        task_message: T,
        # 0 means put without waiting, None means no timeout
        timeout: float | None = None,
    ) -> None:
        # Serializing here, at the boundary, is the whole point: from this line on the
        # buffer deals in bytes it can count rather than an object graph it would have
        # to walk.
        entry = (
            _encode_task_message(task_message),
            task_message.payload,
            type(task_message),
        )
        await super().put(entry=entry, timeout=timeout)

        # Signal the agent wide outbox activity after the buffer released its condition
        # so a get_next_task_message_any waiter can wake and re-scan for this message.
        # Doing it here (outside `self._condition`) means this queue's lock and the
        # agent's `_outbox_activity` are never held at the same time: put takes
        # `self._condition`, releases it, then takes `_outbox_activity`; the waiter only
        # ever holds `_outbox_activity` and never while touching this queue. With the two
        # locks never overlapping no lock ordering cycle can form. The message is already
        # enqueued, so a waiter that scans between the release and this notify finds it
        # directly.
        if self._queue_activity_notifier is not None:
            async with self._queue_activity_notifier:
                self._queue_activity_notifier.notify_all()

    async def get(
        self,
        # 0 means get without waiting, None means no timeout
        timeout: float | None = None,
    ) -> T | object:
        entry = await super().get(timeout=timeout)
        if entry is END_OF_STREAM:
            return entry

        # Decoded after the buffer released its condition. It is synchronous work with no
        # await in it, so holding the lock across it would change nothing about
        # correctness, but there is no reason for one reader's decode to sit inside the
        # lock every other producer and consumer of this queue has to take.
        json_blob, payload, message_type = entry
        return _decode_task_message(
            json_blob=json_blob,
            message_type=message_type,
            payload=payload,
        )

    async def shutdown(self, immediate: bool = False) -> None:
        await super().shutdown(immediate=immediate)

        # Shutdown is a state change the agent wide fan-in must observe, exactly like a
        # put. A get_next_task_message_any waiter parked on `_outbox_activity` is not woken
        # by the buffer-local notify, so without this it would sleep until an unrelated
        # outbox put (or its own timeout) even though this outbox has now reached end of
        # stream. Waking it lets it re-scan, see is_at_end_of_stream, and prune this
        # outbox. Done after the buffer released `self._condition` so this queue's lock
        # and the agent's `_outbox_activity` are never held at once, preserving the lock
        # ordering that put relies on.
        if self._queue_activity_notifier is not None:
            async with self._queue_activity_notifier:
                self._queue_activity_notifier.notify_all()
