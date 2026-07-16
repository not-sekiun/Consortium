import asyncio
import sys

from consortium.framework.agents.agent_message_models import (
    Payload,
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)

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


class TaskMessagesQueue:
    def __init__(self, maximum_memory_size: int | None = None):
        self._queue: asyncio.Queue[tuple[TaskMessage, int]] = asyncio.Queue()
        if maximum_memory_size is not None and maximum_memory_size <= 0:
            raise ValueError("maximum_memory_size must be greater than 0")
        self._maximum_memory_size = maximum_memory_size
        self._current_estimated_memory_size = 0
        # Coordinates producers waiting for space and consumers waiting for
        # messages. notify_all is used whenever either side changes state.
        self._condition = asyncio.Condition()

    def empty(self) -> bool:
        return self._queue.empty()

    def full(self) -> bool:
        if self._maximum_memory_size is None:
            return False
        return self._current_estimated_memory_size >= self._maximum_memory_size

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

    async def put(
        self,
        task_message: TaskMessage,
        timeout: float | None = None,  # 0 means get no wait None means no timeout
    ) -> None:
        size = self._estimate_size(task_message)
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        async with self._condition:
            while not self._can_fit(size):
                if timeout == 0:
                    raise asyncio.QueueFull
                remaining = None if deadline is None else deadline - loop.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError
                try:
                    await asyncio.wait_for(self._condition.wait(), remaining)
                except TimeoutError:
                    raise TimeoutError from None

            self._queue.put_nowait((task_message, size))
            self._current_estimated_memory_size += size
            self._condition.notify_all()

    async def get(
        self, timeout: float | None = None
    ) -> TaskMessage:  # 0 means get no wait None means no timeout never raise an error just return None if we timeout
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        async with self._condition:
            while self._queue.empty():
                if timeout == 0:
                    raise asyncio.QueueEmpty
                remaining = None if deadline is None else deadline - loop.time()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError
                await asyncio.wait_for(self._condition.wait(), remaining)

            task_message, size = self._queue.get_nowait()
            self._current_estimated_memory_size -= size
            self._condition.notify_all()
            return task_message
