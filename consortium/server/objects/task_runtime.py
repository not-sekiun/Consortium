import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from consortium.framework.agents._task_messages_queue import TaskMessagesQueue


class TaskRuntime:
    def __init__(self):
        self._handler: asyncio.Task | None = None
        self._inbox: TaskMessagesQueue | None = None
        self._outbox: TaskMessagesQueue | None = None

    @property
    def handler(self) -> asyncio.Task | None:
        return self._handler

    @property
    def inbox(self) -> TaskMessagesQueue | None:
        return self._inbox

    @property
    def outbox(self) -> TaskMessagesQueue | None:
        return self._outbox

    def attach(
        self,
        handler: asyncio.Task | None,
        inbox: TaskMessagesQueue | None,
        outbox: TaskMessagesQueue | None,
    ) -> None:
        self._handler = handler
        self._inbox = inbox
        self._outbox = outbox

    def has_readable_outbox(self) -> bool:
        return self._outbox is not None and not self._outbox.is_at_end_of_stream()

    def is_exhausted(self) -> bool:
        return self._handler is None and self._inbox is None and self._outbox is None

    def release_handler(self) -> None:
        self._handler = None

    def release_inbox(self) -> None:
        self._inbox = None

    def release_outbox(self) -> None:
        self._outbox = None

    def detach(self) -> list[TaskMessagesQueue]:
        if self._handler is not None:
            self._handler.cancel()

        queues = [queue for queue in (self._inbox, self._outbox) if queue is not None]
        self._handler = None
        self._inbox = None
        self._outbox = None
        return queues
