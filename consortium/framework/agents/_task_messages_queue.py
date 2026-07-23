import asyncio
import sys
import typing

from consortium.framework.agents.agent_message_models import (
    Payload,
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)

if typing.TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent

TaskMessage = TaskLaunchMessageModel | TaskInputMessageModel | TaskOutputMessageModel


def _deep_getsizeof(obj, seen: set[int]) -> int:
    # Recursively estimate the in-memory footprint of a container and its
    # contents. Track seen object ids so shared/cyclic references are only
    # counted once.
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        for key, value in obj.items():
            size += _deep_getsizeof(key, seen)
            size += _deep_getsizeof(value, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            size += _deep_getsizeof(item, seen)
    return size


class TaskMessagesQueue[T: TaskMessage]:
    def __init__(
        self,
        maximum_memory_size: int | None = None,
        agent: Agent | None = None,
    ):
        self._queue: asyncio.Queue[tuple[T, int]] = asyncio.Queue()
        if maximum_memory_size is not None and maximum_memory_size <= 0:
            raise ValueError("maximum_memory_size must be greater than 0")
        self._maximum_memory_size = maximum_memory_size
        self._current_estimated_memory_size = 0
        # Coordinates producers waiting for space and consumers waiting for
        # messages. notify_all is used whenever either side changes state.
        self._condition = asyncio.Condition()
        # Once shut down no further messages may be put. Consumers keep draining any
        # buffered messages, then `get` returns `None` (end of stream). This is the
        # single signal the `drain_*` loops use to know a producer has finished.
        self._shutdown = False
        # When set (the outbox queues are constructed with the owning agent), every
        # successful put also signals the agent's shared outbox activity condition. That
        # lets Agent.get_next_task_message_any wait across all of an agent's capability
        # outboxes at once and wake as soon as any of them receives a message. Left None
        # for queues that do not participate in that fan-in (for example the inbox).
        self._agent = agent

    def _estimate_payload_size(self, payload: Payload) -> int:
        # A streaming payload has no known length until it is consumed, so it
        # cannot be measured up front. Only the object overhead is counted.
        if payload.is_stream:
            return sys.getsizeof(payload)
        return sys.getsizeof(payload) + len(payload.data)

    def _estimate_size(self, task_message: TaskMessage) -> int:
        # Estimate the memory footprint of a message. The binary payload
        # dominates and is measured directly by its byte length; the remaining
        # pydantic fields (dicts, strings, scalars) are estimated recursively.
        seen: set[int] = set()
        size = sys.getsizeof(task_message)
        for field_name in type(task_message).model_fields:
            value = getattr(task_message, field_name)
            if isinstance(value, Payload):
                size += self._estimate_payload_size(value)
            else:
                size += _deep_getsizeof(value, seen)
        return size

    def _can_fit(self, size: int) -> bool:
        if self._maximum_memory_size is None:
            return True
        if self._current_estimated_memory_size + size <= self._maximum_memory_size:
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
        return self._current_estimated_memory_size >= self._maximum_memory_size

    async def put(
        self,
        task_message: T,
        # 0 means get without waiting, None means no timeout
        timeout: float | None = None,
    ) -> None:
        size = self._estimate_size(task_message)
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

            self._queue.put_nowait((task_message, size))
            self._current_estimated_memory_size += size
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
        if self._agent is not None:
            async with self._agent._outbox_activity:
                self._agent._outbox_activity.notify_all()

    async def get(
        self,
        # 0 means get without waiting, None means no timeout
        timeout: float | None = None,
    ) -> T | None:
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        async with self._condition:
            while self._queue.empty():
                # Buffered messages are always served first (above); reaching here
                # with an empty and shut down queue means the producer is finished
                # and nothing more will ever arrive. `None` is the end of stream
                # signal the `drain_*` loops terminate on.
                if self._shutdown:
                    return None
                # timeout=0 falls through to the deadline check and raises
                # immediately; a timeout is "nothing yet, keep waiting", distinct
                # from the `None` end of stream above.
                remaining = None if deadline is None else deadline - loop.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError
                await asyncio.wait_for(self._condition.wait(), remaining)

            task_message, size = self._queue.get_nowait()
            self._current_estimated_memory_size -= size
            self._condition.notify_all()
            return task_message

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
                self._current_estimated_memory_size = 0
            self._condition.notify_all()

        # Shutdown is a state change the agent wide fan-in must observe, exactly like a
        # put. A get_next_task_message_any waiter parked on `_outbox_activity` is not woken
        # by the queue-local notify above, so without this it would sleep until an
        # unrelated outbox put (or its own timeout) even though this outbox has now reached
        # end of stream. Waking it lets it re-scan, see is_at_end_of_stream, and prune this
        # outbox. Done after releasing `self._condition` so this queue's lock and the
        # agent's `_outbox_activity` are never held at once, preserving the lock ordering
        # that put relies on.
        if self._agent is not None:
            async with self._agent._outbox_activity:
                self._agent._outbox_activity.notify_all()
