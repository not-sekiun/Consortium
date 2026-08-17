import asyncio
import sys

import orjson

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

# END_OF_STREAM is the marker `get` returns once a queue has been shut down and fully
# drained: no further messages will ever be produced. It lets readers distinguish an
# exhausted stream from a timeout (which raises TimeoutError) and from a still-open but
# momentarily empty queue. Callers compare against it by identity (`result is
# END_OF_STREAM`).
#
# Defined with the object() trick: a bare, unique object whose only meaningful property
# is its identity. This is a deliberate placeholder for first class sentinel support
# (PEP 661, targeted for Python 3.15), at which point this becomes a proper Sentinel.
END_OF_STREAM = object()


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


class TaskMessagesQueue[T: TaskMessage]:
    def __init__(
        self,
        maximum_memory_size: int | None = None,
        queue_activity_notifier: asyncio.Condition | None = None,
    ):
        self._queue: asyncio.Queue[_QueueEntry] = asyncio.Queue()
        if maximum_memory_size is not None and maximum_memory_size <= 0:
            raise ValueError("maximum_memory_size must be greater than 0")
        self._maximum_memory_size = maximum_memory_size
        self._current_memory_size = 0
        # Coordinates producers waiting for space and consumers waiting for
        # messages. notify_all is used whenever either side changes state.
        self._condition = asyncio.Condition()
        # Once shut down no further messages may be put. Consumers keep draining any
        # buffered messages, then `get` returns END_OF_STREAM. This is the single signal
        # the `drain_*` loops use to know a producer has finished.
        self._shutdown = False
        # When set (the outbox queues are constructed with the owning agent's shared
        # outbox activity condition), every successful put also signals it. That
        # lets Agent.get_next_task_message_any wait across all of an agent's capability
        # outboxes at once and wake as soon as any of them receives a message. Left None
        # for queues that do not participate in that fan-in (for example the inbox).
        self._queue_activity_notifier = queue_activity_notifier

    def _can_fit(self, size: int) -> bool:
        if self._maximum_memory_size is None:
            return True
        if self._current_memory_size + size <= self._maximum_memory_size:
            return True
        # One-time exception: if the queue is empty the message cannot fit
        # anywhere, so admit it regardless of size to avoid blocking forever.
        return self._queue.empty()

    def is_at_end_of_stream(self) -> bool:
        # True once the queue is shut down and fully drained: no more messages will ever
        # be produced (put is closed) and none remain buffered. Readers use this to know
        # an outbox can be discarded. Both reads are plain and lock free; once shut down
        # and empty the state is terminal, so observing it without the lock is safe.
        return self._shutdown and self._queue.empty()

    def empty(self) -> bool:
        return self._queue.empty()

    def full(self) -> bool:
        if self._maximum_memory_size is None:
            return False
        return self._current_memory_size >= self._maximum_memory_size

    async def put(
        self,
        task_message: T,
        # 0 means get without waiting, None means no timeout
        timeout: float | None = None,
    ) -> None:
        # Serializing here, at the boundary, is the whole point: from this line on the
        # queue deals in bytes it can count rather than an object graph it would have to
        # walk.
        json_blob = _encode_task_message(task_message)
        payload = task_message.payload
        message_type = type(task_message)
        size = _task_message_entry_size(json_blob, payload)
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        async with self._condition:
            # A shut down queue accepts no further messages. Unlike a full queue (a
            # transient back pressure condition) this is terminal, so it is a genuine
            # error rather than something to wait out.
            if self._shutdown:
                raise asyncio.QueueShutDown
            while not self._can_fit(size):
                # Queue fullness is used purely for back pressure. We raise
                # TimeoutError (never QueueFull) because the only actionable outcome
                # is "the queue did not make space in time"; timeout=0 falls through
                # to the deadline check below and raises immediately.
                remaining = None if deadline is None else deadline - loop.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError
                await asyncio.wait_for(self._condition.wait(), remaining)
                # A shutdown may have happened while we waited for space.
                if self._shutdown:
                    raise asyncio.QueueShutDown

            self._queue.put_nowait((json_blob, payload, message_type))
            self._current_memory_size += size
            self._condition.notify_all()

        # Signal the agent wide outbox activity after releasing our own condition so a
        # get_next_task_message_any waiter can wake and re-scan for this message. Doing
        # it here (outside `self._condition`) means this queue's lock and the agent's
        # `_outbox_activity` are never held at the same time: put takes `self._condition`,
        # releases it, then takes `_outbox_activity`; the waiter only ever holds
        # `_outbox_activity` and never while touching this queue. With the two locks
        # never overlapping no lock ordering cycle can form. The message is already
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
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        async with self._condition:
            while self._queue.empty():
                # Buffered messages are always served first (above); reaching here
                # with an empty and shut down queue means the producer is finished
                # and nothing more will ever arrive. END_OF_STREAM is the end of
                # stream marker the `drain_*` loops terminate on.
                if self._shutdown:
                    return END_OF_STREAM
                # timeout=0 falls through to the deadline check and raises
                # immediately; a timeout is "nothing yet, keep waiting", distinct
                # from the END_OF_STREAM end of stream above.
                remaining = None if deadline is None else deadline - loop.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError
                await asyncio.wait_for(self._condition.wait(), remaining)

            json_blob, payload, message_type = self._queue.get_nowait()
            # Recomputed rather than stored alongside the entry: it is a pure function
            # of the entry, so it cannot drift from what `put` charged, and keeping it
            # out leaves the entry the 3-tuple the entry overhead accounts for.
            self._current_memory_size -= _task_message_entry_size(json_blob, payload)
            self._condition.notify_all()

        # Decoded after releasing the condition. It is synchronous work with no await in
        # it, so holding the lock across it would change nothing about correctness, but
        # there is no reason for one reader's decode to sit inside the lock every other
        # producer and consumer of this queue has to take.
        return _decode_task_message(
            json_blob=json_blob,
            message_type=message_type,
            payload=payload,
        )

    async def shutdown(self, immediate: bool = False) -> None:
        # Manage our own shutdown state rather than delegating to the underlying
        # asyncio.Queue: waiters block on `self._condition` (not the underlying
        # queue's get/put), so they must be woken via notify_all while holding the
        # condition lock. This is why shutdown is async.
        async with self._condition:
            self._shutdown = True
            if immediate:
                # Drop any buffered messages so consumers see end of stream at once
                # instead of draining the backlog first.
                while not self._queue.empty():
                    self._queue.get_nowait()
                self._current_memory_size = 0
            self._condition.notify_all()

        # Shutdown is a state change the agent wide fan-in must observe, exactly like a
        # put. A get_next_task_message_any waiter parked on `_outbox_activity` is not woken
        # by the queue-local notify above, so without this it would sleep until an
        # unrelated outbox put (or its own timeout) even though this outbox has now reached
        # end of stream. Waking it lets it re-scan, see is_at_end_of_stream, and prune this
        # outbox. Done after releasing `self._condition` so this queue's lock and the
        # agent's `_outbox_activity` are never held at once, preserving the lock ordering
        # that put relies on.
        if self._queue_activity_notifier is not None:
            async with self._queue_activity_notifier:
                self._queue_activity_notifier.notify_all()
