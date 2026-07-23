import asyncio
import typing
from collections.abc import AsyncIterable
from typing import Any

from pydantic import JsonValue

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCommunicationEndOfStreamError,
)
from consortium.framework.agents._task_messages_queue import END_OF_STREAM
from consortium.framework.agents.agent_message_models import (
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)

if typing.TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent
    from consortium.server.objects.agent_task_objects import AgentTask


class _AgentCommunicator:
    def __init__(self, agent: Agent, task: AgentTask):
        from consortium.framework.agents._task_messages_queue import TaskMessagesQueue
        # Importing here to avoid circular import

        self.agent = agent
        self.task = task

        # 8 MB memory capacity for the inbox and outbox
        message_queue_size = 8 * 1024 * 1024
        self._task_messages_inbox = TaskMessagesQueue[TaskOutputMessageModel](
            maximum_memory_size=message_queue_size
        )
        # The outbox is constructed with the owning agent so every put also signals the
        # agent's shared outbox activity condition, letting Agent.get_next_task_message_any
        # wait across all capability outboxes at once. The inbox does not participate in
        # that fan-in so it is left without an agent reference.
        self._task_messages_outbox = TaskMessagesQueue[
            TaskLaunchMessageModel | TaskInputMessageModel
        ](maximum_memory_size=message_queue_size, agent=agent)

    async def send_to_agent(
        self,
        task_message: TaskInputMessageModel | None = None,
        data: dict[str, Any] | None = None,
        payload: bytes | bytearray | AsyncIterable[bytes] | None = None,
        timeout: int | float | None = None,
    ) -> None:
        """Send a message to the agent.

        If a prepared task message is provided it is forwarded to the agent as-is.
        Otherwise a `TaskInputMessageModel` is built from the current task and the
        supplied data and payload before being sent.

        Args:
            task_message: A prepared launch or input message to forward to the agent. If
                provided, `data` and `payload` are ignored.
            data: Structured data to include when building a task input message. Only
                used when `task_message` is None. Defaults to an empty dictionary.
            payload: Optional binary payload to attach when building a task input
                message. Only used when `task_message` is None.
            timeout: Maximum number of seconds to wait for the send to complete. If None,
                waits indefinitely.
        """
        if task_message is not None:
            await self._task_messages_outbox.put(
                task_message=task_message,
                timeout=timeout,
            )
            return

        if data is None:
            data = {}
        task_message = TaskInputMessageModel(
            task_id=self.task.task_id, data=data, payload=payload
        )
        await self._task_messages_outbox.put(
            task_message=task_message,
            timeout=timeout,
        )

    async def recv_from_agent(
        self,
        timeout: int | float | None = None,
    ) -> TaskOutputMessageModel:
        """Wait for and return the next message from the agent.

        Blocks until the next result message for this task is available on the agent's
        result messages queue.

        Args:
            timeout: Maximum number of seconds to wait for a message. If None, waits
                indefinitely.

        Returns:
            The next task output message received from the agent.

        Raises:
            TimeoutError: If `timeout` is set and no message arrives within it.
            AgentCommunicationEndOfStreamError: If the inbox reaches end of stream while
                waiting. A communicator is coordinated with the remote endpoint, so this
                should never happen during normal operation.
        """
        if timeout is None:
            task_message = await self._task_messages_inbox.get()
        else:
            task_message = await self._task_messages_inbox.get(timeout=timeout)

        # A communicator is coordinated with the remote endpoint for the lifetime of the
        # task, so it should never observe end of stream (END_OF_STREAM from the inbox)
        # while waiting for a result. If it does the inbox was shut down out from under a
        # coordinated read, which is a genuine error rather than the normal termination
        # signal the outbox-side readers rely on.
        if task_message is END_OF_STREAM:
            raise AgentCommunicationEndOfStreamError(
                agent_id=str(self.agent.agent_id),
                name=self.agent.name,
                task_id=str(self.task.task_id),
                command=self.task.command,
            )

        return task_message

    async def send_and_recv_from_agent(
        self,
        task_message: TaskInputMessageModel | None = None,
        data: dict[str, Any] | None = None,
        payload: bytes | bytearray | AsyncIterable[bytes] | None = None,
        timeout: int | float | None = None,
    ) -> TaskOutputMessageModel:
        """Send a message to the agent and wait for its response.

        Combines `send_to_agent` and `recv_from_agent` into a single round trip. When a
        timeout is provided, it applies to the combined send-and-receive operation.

        Args:
            task_message: A prepared launch or input message to forward to the agent. If
                provided, `data` and `payload` are ignored.
            data: Structured data to include when building a task input message. Only
                used when `task_message` is None.
            payload: Optional binary payload to attach when building a task input
                message. Only used when `task_message` is None.
            timeout: Maximum number of seconds to wait for the combined send and receive
                to complete. If None, waits indefinitely.

        Returns:
            The task output message received from the agent in response.

        Raises:
            TimeoutError: If `timeout` is set and the combined operation does not
                complete within it.
        """
        if timeout is None:
            await self.send_to_agent(
                task_message=task_message,
                data=data,
                payload=payload,
            )
            return await self.recv_from_agent()

        async with asyncio.timeout(timeout):
            await self.send_to_agent(
                task_message=task_message,
                data=data,
                payload=payload,
            )
            return await self.recv_from_agent()

    def create_task_input_message(
        self, data: dict[str, JsonValue] | None = None
    ) -> TaskInputMessageModel:
        data = data if data is not None else {}
        return TaskInputMessageModel(task_id=self.task.task_id, data=data)
