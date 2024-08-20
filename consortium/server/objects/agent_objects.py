import asyncio
import uuid
from datetime import datetime
from typing import Any

from consortium.framework.base_agent_capability import (
    AgentCapabilityCommunicationModel,
    BaseAgentCapability,
)
from consortium.framework.c2_types import BaseAgentType
from consortium.server.exceptions.framework_exceptions.agents_framework_exceptions import (
    AgentCapabilityNotFoundError,
    AgentResultHasNoCorrespondingTaskError,
    AgentResultIDNotFoundError,
    AgentResultTaskIDNotFoundError,
    AgentTaskNotFoundError,
)
from consortium.server.models.agent_models import (
    AgentMessageModel,
    AgentResultModel,
    AgentResultState,
    AgentTaskModel,
    AgentTaskState,
)


class Agent:
    def __init__(
        self,
        agent_type: BaseAgentType,
        name: str = "",
        description: str = "",
        endpoint: str = "",
        is_admin: bool | None = None,
        os: str | None = None,
        version: str | None = None,
        arch: str | None = None,
        pid: int | None = None,
        locale: str | None = None,
        remote_host_address: str | None = None,
        local_host_address: str | None = None,
        agent_data: dict[str, Any] | None = None,
    ):
        if agent_data is None:
            agent_data = {}

        # TODO: Add data validation
        self.agent_id = uuid.uuid4()
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.is_admin = is_admin
        self.os = os
        self.version = version
        self.arch = arch
        self.pid = pid
        self.locale = locale
        self.remote_host_address = remote_host_address
        self.local_host_address = local_host_address
        self.agent_data = agent_data

        self.datetime_first_checked_in = datetime.now()
        self.datetime_last_checked_in = datetime.now()

        # TODO: Move all the tasks and results to a database instead of storing them
        #  all in memory.
        self._queued_tasks = {}
        self._running_tasks = {}
        self._completed_tasks = {}
        self._results = {}

        self._agent_messages_queue = asyncio.Queue()
        self._agent_responses_queue = asyncio.Queue()
        self._agent_capability_handlers = set()

    def __repr__(self) -> str:
        return (
            f"Agent(name={self.name!r}, description={self.description!r}), "
            f"agent_data={self.agent_data!r})"
        )

    def __str__(self) -> str:
        return f'"{self.name}" ({self.agent_id})'

    def add_task(self, task: AgentTaskModel) -> None:
        parsed_initial_agent_message_from_agent_task = AgentMessageModel(
            task_id=task.task_id,
            command=task.command,
            arguments=task.arguments,
        )

        async def _agent_capability_handler(
            handled_agent_capability: BaseAgentCapability,
            initial_agent_message: AgentMessageModel,
        ):
            async for agent_message in handled_agent_capability.on_agent_message_sent(
                agent_message=initial_agent_message,
            ):
                await self._agent_messages_queue.put(agent_message)

        self._queued_tasks[str(task.task_id)] = task

        for agent_capability in self.agent_type.agent_capabilities:
            if agent_capability.name == task.command:
                agent_capability_task = asyncio.create_task(
                    _agent_capability_handler(
                        handled_agent_capability=agent_capability,
                        initial_agent_message=parsed_initial_agent_message_from_agent_task,
                    ),
                )
                self._agent_capability_handlers.add(agent_capability_task)
                return
        raise AgentCapabilityNotFoundError(
            command=task.command,
            agent_str=str(self),
            agent_type_str=str(self.agent_type),
        )

    def get_next_agent_message_without_waiting(self) -> AgentTaskModel | None:
        try:
            return self._agent_messages_queue.get_nowait()
        except asyncio.queues.QueueEmpty:
            return None

    async def get_next_agent_message_with_waiting(self) -> AgentTaskModel:
        return await self._agent_messages_queue.get()

    # This function is one which returns a list of tasks but doesn't actually remove
    # them from the queued tasks list or consider them to be running once returned. It
    # is purely used just to look at the current state of a queued task.
    def get_all_queued_tasks(self) -> list[AgentTaskModel]:
        return list(self._queued_tasks)

    def get_queued_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        try:
            return self._queued_tasks[task_id]
        except KeyError:
            raise AgentTaskNotFoundError(task_id=task_id)

    def get_all_running_tasks(self) -> list[AgentTaskModel]:
        return list(self._running_tasks)

    def get_running_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        try:
            return self._running_tasks[task_id]
        except KeyError:
            raise AgentTaskNotFoundError(task_id=task_id)

    def get_all_completed_tasks(self) -> list[AgentTaskModel]:
        return list(self._completed_tasks)

    def get_completed_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        try:
            return self._completed_tasks[task_id]
        except KeyError:
            raise AgentTaskNotFoundError(task_id=task_id)

    def get_all_tasks(self) -> list[AgentTaskModel]:
        return [
            *self._queued_tasks.values(),
            *self._running_tasks.values(),
            *self._completed_tasks.values(),
        ]

    def get_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        for task in self.get_all_tasks():
            if task_id == str(task.task_id):
                return task
        raise AgentTaskNotFoundError(task_id=task_id)

    def delete_queued_task_by_task_id(self, task_id: str):
        try:
            self._queued_tasks.pop(task_id)
        except KeyError:
            raise AgentTaskNotFoundError(task_id=task_id)

    def add_result(self, result: AgentResultModel) -> None:
        if result.task_id not in self._running_tasks:
            raise AgentResultHasNoCorrespondingTaskError(
                result_id=str(result.result_id),
                corresponding_task_id=result.task_id,
                agent_str=str(self),
            )
        self._results[str(result.result_id)] = result

        # Adding the result implies that the task is completed.
        task = self._running_tasks.pop(result.task_id)
        task.state = AgentTaskState.COMPLETED
        self._completed_tasks[str(task.task_id)] = task

    def get_all_results(self) -> list[AgentResultModel]:
        return list(self._results.values())

    def get_all_successful_results(self) -> list[AgentResultModel]:
        return [
            result
            for result in self._results.values()
            if result.status == AgentResultState.SUCCESS
        ]

    def get_all_failed_results(self) -> list[AgentResultModel]:
        return [
            result
            for result in self._results.values()
            if result.status == AgentResultState.FAILED
        ]

    def get_all_errored_results(self) -> list[AgentResultModel]:
        return [
            result
            for result in self._results.values()
            if result.status == AgentResultState.ERRORED
        ]

    def get_result_by_task_id(self, task_id: str) -> AgentResultModel:
        for result in self._results.values():
            if result.task_id == task_id:
                return result
        raise AgentResultTaskIDNotFoundError(task_id=task_id)

    def get_result_by_result_id(self, result_id: str) -> AgentResultModel:
        try:
            return self._results[result_id]
        except KeyError:
            raise AgentResultIDNotFoundError(result_id=result_id)

    def to_json(self) -> dict:
        return {
            "agent_id": str(self.agent_id),
            "agent_type": str(self.agent_type),
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "is_admin": self.is_admin,
            "os": self.os,
            "version": self.version,
            "arch": self.arch,
            "pid": self.pid,
            "locale": self.locale,
            "remote_host_address": self.remote_host_address,
            "local_host_address": self.local_host_address,
            "datetime_first_checked_in": self.datetime_first_checked_in.isoformat(),
            "datetime_last_checked_in": self.datetime_last_checked_in.isoformat(),
            "agent_data": self.agent_data,
        }
