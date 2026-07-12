import asyncio
import typing
from collections.abc import AsyncIterable
from typing import Any

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
        self.agent = agent
        self.task = task
        # The agent result messages queue is per agent capability and serves to
        # demultiplex messages coming in from the listener.
        self.result_messages_queue = asyncio.Queue()

    async def send_to_agent(
        self,
        task_message: TaskLaunchMessageModel | TaskInputMessageModel | None = None,
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
            await self.agent.send_task_message(
                task_message=task_message,
                timeout=timeout,
            )
            return

        if data is None:
            data = {}
        task_message = TaskInputMessageModel(
            task_id=self.task.task_id, data=data, payload=payload
        )
        await self.agent.send_task_message(
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
        """
        if timeout is None:
            return await self.result_messages_queue.get()

        return await asyncio.wait_for(
            self.result_messages_queue.get(),
            timeout=timeout,
        )

    async def send_and_recv_from_agent(
        self,
        task_message: TaskLaunchMessageModel | TaskInputMessageModel | None = None,
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
