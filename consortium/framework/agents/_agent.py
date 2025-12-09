import asyncio
import uuid
from datetime import datetime
from typing import Any, Type

from loguru import logger

from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server import server_singletons as server_singletons
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
        hostname: str | None = None,
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
        self.hostname = hostname
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

        self._events_service = server_singletons.events_service
        self._agent_task_messages_queue = asyncio.Queue()
        # Each agent capability is mapped to a task by the task ID. This lets us
        # distinguish which capability a response should be sent to even if the same
        # type of agent capability is running.
        self._running_agent_capabilities = {}
        # Agent capabilities run as asyncio tasks, we add them to a set to prevent
        # their garbage collection.
        self._agent_capability_tasks = set()

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

    def _move_queued_task_to_running(self, task_id: str) -> None:
        task = self._queued_tasks.pop(task_id)
        task.environment = AgentTaskState.RUNNING
        self._running_tasks[str(task.task_id)] = task

    def _move_running_task_to_completed(self, task_id: str) -> None:
        task = self._running_tasks.pop(task_id)
        task.environment = AgentTaskState.COMPLETED
        self._completed_tasks[str(task.task_id)] = task

    async def _manage_running_agent_capability(
        self,
        agent_capability: Type[BaseAgentCapability],
        agent_task_message: AgentTaskMessageModel,
    ) -> None:
        async def agent_capability_task_handler(
            agent_capability: BaseAgentCapability,
            agent_task_message: AgentTaskMessageModel,
        ):
            result_message = await agent_capability.run_agent_capability(
                agent_task_message=agent_task_message,
            )

            # Upon receiving the final aggregated result message we can remove the
            # agent capability as it is now no longer considered to be running.
            self._running_agent_capabilities.pop(str(agent_task_message.task_id))

            result = AgentResultModel(
                result_id=result_message.result_id,
                success=result_message.success,
                message=result_message.message,
                data=result_message.data,
                task_id=result_message.task_id,
            )
            self._results[str(result.result_id)] = result

            # Adding the result implies that the task is completed so we can now move
            # the task from the running tasks to the completed tasks.
            self._move_running_task_to_completed(
                task_id=str(result_message.task_id),
            )

            # Finally we fire the event to notify all event handlers that a result has
            # been received.
            await self._events_service.trigger_event(
                event=Event(
                    event_type=EventType.AGENT_RESULT_RECEIVED,
                    data={
                        "agent_id": str(self.agent_id),
                        "result_id": str(result.result_id),
                    },
                ),
            )

        running_agent_capability = agent_capability(
            agent_task_messages_queue=self._agent_task_messages_queue,
        )
        self._running_agent_capabilities[str(agent_task_message.task_id)] = (
            running_agent_capability
        )

        agent_capability_task = asyncio.create_task(
            agent_capability_task_handler(
                agent_capability=running_agent_capability,
                agent_task_message=agent_task_message,
            ),
        )
        self._agent_capability_tasks.add(agent_capability_task)
        # Once the task is finished we have it automatically remove its own reference
        # within the set to avoid holding references to finished tasks indefinitely.
        agent_capability_task.add_done_callback(self._agent_capability_tasks.discard)

    async def add_task(self, task: AgentTaskModel) -> None:
        for agent_capability in self.agent_type.agent_capabilities:
            if agent_capability.name == task.command:
                # Perform validation on the parameters passed to the options of a
                # particular agent capability.
                for argument_name, argument_value in task.arguments.items():
                    if argument_name not in agent_capability.options:
                        raise AgentCapabilityArgumentNotFoundError(
                            command=agent_capability.name,
                            argument=argument_name,
                            agent_str=str(self),
                            agent_type_str=str(self.agent_type),
                        )
                    # This specific statement allows two methods of passing in value
                    # for an option that is not required. The REST API JSON data can
                    # either contain the key with a value of None or not contain the
                    # key at all. Either way, we avoid setting any value for the option.
                    if argument_value is None:
                        continue
                    # `OptionValueValidationError` is raised here on failure to validate
                    # the value when we attempt to set it.
                    agent_capability.options[argument_name].set_option_value(
                        value=argument_value,
                    )

                self._queued_tasks[str(task.task_id)] = task

                # Now we construct the arguments dictionary based on the options. If no
                # value was provided for a particular option this process will grab the
                # default value from the option. If no default value or value was
                # provided then this process will raise a `RequiredOptionNotSetError`
                # exception.
                arguments = {}
                for (
                    argument_name,
                    argument_option,
                ) in agent_capability.options.items():
                    arguments[argument_name] = argument_option.get_option_value()
                    # After getting the value from setting the option we have to clear
                    # the option to prevent the value from persisting across different
                    # taskings.
                    argument_option.clear_option_value()
                # Strip redundant information from the task to create a task message.
                initial_agent_message = AgentTaskMessageModel(
                    task_id=task.task_id,
                    command=task.command,
                    arguments=arguments,
                )
                await self._manage_running_agent_capability(
                    agent_capability=agent_capability,
                    agent_task_message=initial_agent_message,
                )

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
                self._move_queued_task_to_running(task_id=str(message.task_id))
            return message
        except asyncio.queues.QueueEmpty:
            return None

    async def get_next_task_message_with_waiting(self) -> AgentTaskMessageModel:
        message = await self._agent_task_messages_queue.get()
        if str(message.task_id) in self._queued_tasks:
            self._move_queued_task_to_running(task_id=str(message.task_id))
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

        agent_capability = self._running_agent_capabilities[str(result_message.task_id)]
        await agent_capability.agent_result_messages_queue.put(result_message)

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
            "hostname": self.hostname,
            "datetime_first_checked_in": self.datetime_first_checked_in.isoformat(),
            "datetime_last_checked_in": self.datetime_last_checked_in.isoformat(),
            "agent_data": self.agent_data,
        }
