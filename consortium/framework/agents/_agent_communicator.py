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
