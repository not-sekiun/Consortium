import asyncio
import uuid
from datetime import datetime
from typing import Any

from loguru import logger

from consortium.framework.base_agent_capability import BaseAgentCapability
from consortium.framework.c2_types import BaseAgentType
from consortium.server.exceptions.framework_exceptions.agents_framework_exceptions import (
    AgentCapabilityArgumentNotFoundError,
    AgentCapabilityNotFoundError,
    AgentResultHasNoCorrespondingTaskError,
    AgentResultIDNotFoundError,
    AgentResultTaskIDNotFoundError,
    AgentTaskNotFoundError,
)
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentResultModel,
    AgentTaskMessageModel,
    AgentTaskModel,
    AgentTaskState,
)
from consortium.server.server_logging import LoggerType


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

        self.agent_logger = logger.bind(
            logger_name=f"Agent {self}",
            logger_type=LoggerType.AGENT_LOGGER,
        )
        self.datetime_first_checked_in = datetime.now()
        self.datetime_last_checked_in = datetime.now()

        # TODO: Move all the tasks and results to a database instead of storing them
        #  all in memory.
        self._queued_tasks = {}
        self._running_tasks = {}
        self._completed_tasks = {}
        self._results = {}

        self._agent_task_messages_queue = asyncio.Queue()
        # Each agent capability is mapped to a task by the task ID. This lets us
        # distinguish which capability a response should be sent to even if the same
        # type of agent capability is running.
        self._pending_agent_capability_response_message_handlers = {}
        # Task message handlers run as asyncio tasks, we add them to a set to prevent
        # their garbage collection.
        self._agent_task_message_handler_tasks = set()

    def __repr__(self) -> str:
        return (
            f"Agent(agent_type={self.agent_type!r}, name={self.name!r}, "
            f"description={self.description!r}, endpoint={self.endpoint!r}, "
            f"is_admin={self.is_admin!r}, os={self.os!r}, version={self.version!r}, "
            f"arch={self.arch!r}, pid={self.pid!r}, locale={self.locale!r}, "
            f"remote_host_address={self.remote_host_address!r}, "
            f"local_host_address={self.local_host_address!r}, "
            f"agent_data={self.agent_data!r})"
        )

    def __str__(self) -> str:
        return f"'{self.name}' ({self.agent_id})"

    async def add_task(self, task: AgentTaskModel) -> None:
        parsed_initial_agent_message_from_agent_task = AgentTaskMessageModel(
            task_id=task.task_id,
            command=task.command,
            arguments=task.arguments,
        )

        # The agent capability defines a method to handle whenever an agent gets sent a
        # new task. This method receives as input the task message (the task but with
        # non-essential information, e.g. the datetime the task was created, stripped).
        # This method then yields further additional task messages that are to be sent
        # out to the wire. This handler collects those yielded messages and puts them
        # into a task message-aggregating queue to be consumed by the listener before
        # sending out to the wire.
        async def _agent_capability_task_messages_generator_handler(
            handled_agent_capability: BaseAgentCapability,
            initial_agent_message: AgentTaskMessageModel,
        ):
            async for (
                agent_message
            ) in handled_agent_capability.handle_sending_agent_task_messages(
                agent_message=initial_agent_message,
            ):
                await self._agent_task_messages_queue.put(agent_message)

        for agent_capability in self.agent_type.agent_capabilities:
            if agent_capability.name == task.command:
                # Perform validation on the parameters passed to the options of a
                # particular agent capability.
                for argument_name, argument_value in task.arguments.items():
                    if argument_name not in agent_capability.arguments:
                        raise AgentCapabilityArgumentNotFoundError(
                            command=agent_capability.name,
                            argument=argument_name,
                            agent_str=str(self),
                            agent_type_str=str(self.agent_type),
                        )
                    # This specific statement allows two methods of passing in value
                    # for an option that is not required. The REST API JSON data can
                    # either contain the key with a value of None or not contain the
                    # key at all.
                    if argument_value is None:
                        continue
                    # OptionValueValidationError is raised here on failure to validate
                    # the value.
                    agent_capability.arguments[argument_name].validate_value(
                        argument_value,
                    )

                self._queued_tasks[str(task.task_id)] = task
                agent_capability_task_handler = asyncio.create_task(
                    _agent_capability_task_messages_generator_handler(
                        handled_agent_capability=agent_capability,
                        initial_agent_message=parsed_initial_agent_message_from_agent_task,
                    ),
                )
                # Add the task to a set to prevent its garbage collection.
                self._agent_task_message_handler_tasks.add(
                    agent_capability_task_handler,
                )
                # Here we create the generator (but we don't run it yet) to prime it to
                # get ready to handle the response messages.
                agent_capability_response_messages_handler = (
                    agent_capability.handle_receiving_agent_response_messages()
                )
                self._pending_agent_capability_response_message_handlers[
                    str(task.task_id)
                ] = agent_capability_response_messages_handler
                return
        raise AgentCapabilityNotFoundError(
            command=task.command,
            agent_str=str(self),
            agent_type_str=str(self.agent_type),
        )

    def get_next_task_message_without_waiting(self) -> AgentTaskMessageModel | None:
        try:
            message = self._agent_task_messages_queue.get_nowait()
            if str(message.task_id) in self._queued_tasks:
                running_task = self._queued_tasks.pop(str(message.task_id))
                self._running_tasks[str(running_task.task_id)] = running_task
            return message
        except asyncio.queues.QueueEmpty:
            return None

    async def get_next_task_message_with_waiting(self) -> AgentTaskMessageModel:
        message = await self._agent_task_messages_queue.get()
        if str(message.task_id) in self._queued_tasks:
            running_task = self._queued_tasks.pop(str(message.task_id))
            self._running_tasks[str(running_task.task_id)] = running_task
        return message

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

    async def add_result_message(self, result_message: AgentResultMessageModel) -> None:
        if str(result_message.task_id) not in self._running_tasks:
            raise AgentResultHasNoCorrespondingTaskError(
                result_id=str(result_message.result_id),
                corresponding_task_id=str(result_message.task_id),
                agent_str=str(self),
            )

        pending_agent_capability_response_message_handler = (
            self._pending_agent_capability_response_message_handlers[
                str(result_message.task_id)
            ]
        )

        try:
            response_message = (
                await pending_agent_capability_response_message_handler.asend(
                    result_message,
                )
            )
        # `TypeError` is raised when we attempt to yield from a non-started
        # generator.
        except TypeError:
            # The response message handler generator was created but not
            # started yet, so we attempt to start the generator first by
            # sending a null value.
            await pending_agent_capability_response_message_handler.asend(
                None,
            )
            response_message = (
                await pending_agent_capability_response_message_handler.asend(
                    result_message,
                )
            )

        if response_message:
            del self._pending_agent_capability_response_message_handlers[
                str(result_message.task_id)
            ]

            result = AgentResultModel(
                result_id=result_message.result_id,
                success=result_message.success,
                message=result_message.message,
                data=result_message.data,
                task_id=result_message.task_id,
            )
            self._results[str(result.result_id)] = result

            # Adding the result implies that the task is completed.
            task = self._running_tasks.pop(str(result_message.task_id))
            task.state = AgentTaskState.COMPLETED
            self._completed_tasks[str(task.task_id)] = task

    def get_all_results(self) -> list[AgentResultModel]:
        return list(self._results.values())

    def get_all_successful_results(self) -> list[AgentResultModel]:
        return [result for result in self._results.values() if result.success]

    def get_all_failed_results(self) -> list[AgentResultModel]:
        return [result for result in self._results.values() if not result.success]

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
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "agent_type": self.agent_type.to_json(),
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
