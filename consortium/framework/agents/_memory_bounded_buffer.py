import asyncio
from collections.abc import Callable

# END_OF_STREAM is the marker `get` returns once a buffer has been shut down and fully
# drained: no further entries will ever be produced. It lets readers distinguish an
# exhausted stream from a timeout (which raises TimeoutError) and from a still-open but
# momentarily empty buffer. Callers compare against it by identity (`result is
# END_OF_STREAM`).
#
# Defined with the object() trick: a bare, unique object whose only meaningful property
# is its identity. This is a deliberate placeholder for first class sentinel support
# (PEP 661, targeted for Python 3.15), at which point this becomes a proper Sentinel.
END_OF_STREAM = object()


# A FIFO whose depth is measured in bytes rather than entries, with back pressure on the
# producer and a terminal end of stream signal for the consumer. It knows nothing about
# what an entry is: sizing is supplied by the caller, so a subclass decides what it
# stores and what that costs. Subclasses may narrow `put`/`get` to their own entry type.
class MemoryBoundedBuffer[T]:
    def __init__(
        self,
        entry_size: Callable[[T], int],
        maximum_memory_size: int | None = None,
    ):
        self._queue: asyncio.Queue[T] = asyncio.Queue()
        if maximum_memory_size is not None and maximum_memory_size <= 0:
            raise ValueError("maximum_memory_size must be greater than 0")
        self._entry_size = entry_size
        self._maximum_memory_size = maximum_memory_size
        self._current_memory_size = 0
        # Coordinates producers waiting for space and consumers waiting for entries.
        # notify_all is used whenever either side changes state.
        self._condition = asyncio.Condition()
        # Once shut down no further entries may be put. Consumers keep draining any
        # buffered entries, then `get` returns END_OF_STREAM. This is the single signal
        # drain loops use to know a producer has finished.
        self._shutdown = False

    def _can_fit(self, size: int) -> bool:
        if self._maximum_memory_size is None:
            return True
        if self._current_memory_size + size <= self._maximum_memory_size:
            return True
        # One-time exception: if the buffer is empty the entry cannot fit anywhere, so
        # admit it regardless of size to avoid blocking forever.
        return self._queue.empty()

    def is_at_end_of_stream(self) -> bool:
        # True once the buffer is shut down and fully drained: no more entries will ever
        # be produced (put is closed) and none remain buffered. Readers use this to know
        # it can be discarded. Both reads are plain and lock free; once shut down and
        # empty the state is terminal, so observing it without the lock is safe.
        return self._shutdown and self._queue.empty()

    def empty(self) -> bool:
        return self._queue.empty()

    def full(self) -> bool:
        if self._maximum_memory_size is None:
            return False
        return self._current_memory_size >= self._maximum_memory_size

    async def put(
        self,
        entry: T,
        # 0 means put without waiting, None means no timeout
        timeout: float | None = None,
    ) -> None:
        size = self._entry_size(entry)
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        async with self._condition:
            # A shut down buffer accepts no further entries. Unlike a full buffer (a
            # transient back pressure condition) this is terminal, so it is a genuine
            # error rather than something to wait out.
            if self._shutdown:
                raise asyncio.QueueShutDown
            while not self._can_fit(size):
                # Fullness is used purely for back pressure. We raise TimeoutError
                # (never QueueFull) because the only actionable outcome is "the buffer
                # did not make space in time"; timeout=0 falls through to the deadline
                # check below and raises immediately.
                remaining = None if deadline is None else deadline - loop.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError
                await asyncio.wait_for(self._condition.wait(), remaining)
                # A shutdown may have happened while we waited for space.
                if self._shutdown:
                    raise asyncio.QueueShutDown

            self._queue.put_nowait(entry)
            self._current_memory_size += size
            self._condition.notify_all()

    async def get(
        self,
        # 0 means get without waiting, None means no timeout
        timeout: float | None = None,
    ) -> T | object:
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        async with self._condition:
            while self._queue.empty():
                # Buffered entries are always served first (above); reaching here with
                # an empty and shut down buffer means the producer is finished and
                # nothing more will ever arrive.
                if self._shutdown:
                    return END_OF_STREAM
                # timeout=0 falls through to the deadline check and raises immediately;
                # a timeout is "nothing yet, keep waiting", distinct from the
                # END_OF_STREAM end of stream above.
                remaining = None if deadline is None else deadline - loop.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError
                await asyncio.wait_for(self._condition.wait(), remaining)

            entry = self._queue.get_nowait()
            # Recomputed rather than stored alongside the entry: it is a pure function of
            # the entry, so it cannot drift from what `put` charged, and keeping it out
            # leaves the entry exactly what the producer handed over.
            self._current_memory_size -= self._entry_size(entry)
            self._condition.notify_all()

        return entry

    async def shutdown(self, immediate: bool = False) -> None:
        # Manage our own shutdown state rather than delegating to the underlying
        # asyncio.Queue: waiters block on `self._condition` (not the underlying queue's
        # get/put), so they must be woken via notify_all while holding the condition
        # lock. This is why shutdown is async.
        async with self._condition:
            self._shutdown = True
            if immediate:
                # Drop any buffered entries so consumers see end of stream at once
                # instead of draining the backlog first.
                while not self._queue.empty():
                    self._queue.get_nowait()
                self._current_memory_size = 0
            self._condition.notify_all()
