import asyncio
import uuid
from datetime import datetime
from typing import Any, get_type_hints

from loguru import logger
from pydantic import BaseModel, ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework.agents.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.framework_exceptions.agents_framework_exceptions import (
    AgentCapabilityNotFoundError,
    AgentCapabilityOptionNotFoundError,
    AgentCapabilityOptionValueValidationError,
    AgentCreationParameterTypeError,
    AgentResultHasNoCorrespondingTaskError,
    AgentResultIDNotFoundError,
    AgentResultTaskIDNotFoundError,
    AgentTaskNotFoundError,
    AgentTypeResolutionError,
    MissingRequiredAgentCapabilityOptionError,
)
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.service_exceptions.c2_types_service_exceptions import (
    AgentTypeNotFoundError,
)
from consortium.server.exceptions.service_exceptions.payloads_service_exceptions import (
    PayloadNotFoundError,
)
from consortium.server.models.agent_models import (
    AgentResultModel,
    AgentTaskModel,
    AgentTaskState,
)
from consortium.server.server_logging import LoggerType


class _AgentParametersModel(BaseModel):
    payload_id: str | None = (None,)
    agent_type: str | None
    name: str
    description: str
    endpoint: str
    is_admin: bool | None
    os: str | None
    version: str | None
    arch: str | None
    pid: int | None
    locale: str | None
    remote_host_address: str | None
    local_host_address: str | None
    hostname: str | None
    agent_data: dict[str, Any] | None


class Agent:
    def __init__(
        self,
        payload_id: str | None = None,
        agent_type: str | None = None,
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

        try:
            _AgentParametersModel(
                payload_id=payload_id,
                agent_type=agent_type,
                name=name,
                description=description,
                endpoint=endpoint,
                is_admin=is_admin,
                os=os,
                version=version,
                arch=arch,
                pid=pid,
                locale=locale,
                remote_host_address=remote_host_address,
                local_host_address=local_host_address,
                hostname=hostname,
                agent_data=agent_data,
            )
        except ValidationError as exc:
            raise AgentCreationParameterTypeError(
                parameter_name=exc.errors()[0]["loc"][0],
                parameter_type=get_type_hints(_AgentParametersModel)[
                    exc.errors()[0]["loc"]
                ],
            ) from None

        self.agent_id = uuid.uuid4()

        # An agent must have an agent type to be able to be tasked and receive results.
        # if no agent type identifier is provided via either the payload ID or the agent
        # type name then we cannot resolve the agent type and must not allow the agent
        # to exist.
        if payload_id is None and agent_type is None:
            raise AgentTypeResolutionError.due_to_no_identifier_provided()
        # Attempt to resolve the agent type via the payload ID if one was provided.
        if payload_id is not None:
            try:
                payload = server_singletons.payloads_service.get_payload_by_payload_id(
                    payload_id=payload_id
                )
                self.agent_type = payload.agent_type
            except PayloadNotFoundError:
                raise AgentTypeResolutionError.due_to_payload_not_found_error(
                    payload_id=payload_id,
                ) from None
        # Attempt to resolve the agent type via the agent type if one was provided.
        if agent_type is not None:
            try:
                self.agent_type = (
                    server_singletons.c2_types_service.get_agent_type_by_name(
                        agent_type_name=agent_type,
                    )
                )
            except AgentTypeNotFoundError:
                raise AgentTypeResolutionError.due_to_agent_type_not_found_error(
                    agent_type_name=agent_type,
                ) from None

        self.payload_id = payload_id
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
        self._task_messages_queue = asyncio.Queue()
        self._task_messages_queue_lock = asyncio.Lock()
        # Each agent capability is mapped to a task by the task ID. This lets us
        # distinguish which capability a response should be sent to even if the same
        # type of agent capability is running.
        self._running_agent_capabilities = {}
        # Agent capabilities run as asyncio tasks, we add them to a set to prevent
        # their garbage collection.
        self._agent_capability_tasks = set()

    def __repr__(self) -> str:
        return (
            f"Agent("
            f"agent_type={self.agent_type!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"endpoint={self.endpoint!r}, "
            f"is_admin={self.is_admin!r}, "
            f"os={self.os!r}, "
            f"version={self.version!r}, "
            f"arch={self.arch!r}, "
            f"pid={self.pid!r}, "
            f"locale={self.locale!r}, "
            f"remote_host_address={self.remote_host_address!r}, "
            f"local_host_address={self.local_host_address!r}, "
            f"agent_data={self.agent_data!r}"
            f")"
        )

    def __str__(self) -> str:
        return f"'{self.name}' ({self.agent_id})"

    async def add_task(self, task: AgentTaskModel) -> None:
        # TODO: Convert this to use a lookup dictionary instead of iterating through
        #  all agent capabilities.
        for agent_capability in self.agent_type.agent_capabilities:
            if agent_capability.name == task.command:
                arguments = task.arguments

                # Fill in default option values for options that were not provided in the
                # arguments dictionary. For options that do not have a default value
                # they fill in as `None`
                for option_name, option in agent_capability.options.items():
                    if option_name not in arguments:
                        arguments[option_name] = option.default_value

                # Validate entire constructed argument set before creating the listener.
                for option_name, value in arguments.items():
                    if option_name not in agent_capability.options:
                        raise AgentCapabilityOptionNotFoundError(
                            command=agent_capability.name,
                            option_name=option_name,
                            agent_str=str(self),
                            agent_type_str=str(self.agent_type),
                        )
                    try:
                        option = agent_capability.options[option_name]
                        # Allow `None` for non-required options
                        if value is None and not option.required:
                            continue
                        option.validate_value(value)
                    except OptionValueValidationError as exc:
                        raise AgentCapabilityOptionValueValidationError(
                            option_name=option_name,
                            option_value=value,
                            agent_str=str(self),
                            error_message=str(exc),
                        ) from None

                # Check for missing required options.
                for option_name, option in agent_capability.options.items():
                    if option.required and option_name not in arguments:
                        raise MissingRequiredAgentCapabilityOptionError(
                            agent_str=str(self),
                            agent_capability_name=agent_capability.name,
                            option_name=option_name,
                        )

                # Run validation function on the entire set of arguments if one was provided.
                if agent_capability.validating_function:
                    agent_capability.validating_function(arguments)

                self._queued_tasks[str(task.task_id)] = task

                # Strip redundant information from the task to create a task message.
                initial_agent_message = AgentTaskMessageModel(
                    task_id=task.task_id,
                    command=task.command,
                    arguments=arguments,
                )
                await self._start_agent_capability(
                    agent_capability=agent_capability,
                    task_message=initial_agent_message,
                )
                return
        raise AgentCapabilityNotFoundError(
            command=task.command,
            agent_str=str(self),
            agent_type_str=str(self.agent_type),
        )

    def get_next_task_message_without_waiting(self) -> AgentTaskMessageModel | None:
        try:
            message = self._task_messages_queue.get_nowait()
            if str(message.task_id) in self._queued_tasks:
                self._move_queued_task_to_running(task_id=str(message.task_id))
            return message
        except asyncio.queues.QueueEmpty:
            return None

    async def get_next_task_message_with_waiting(self) -> AgentTaskMessageModel:
        message = await self._task_messages_queue.get()
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
            raise AgentTaskNotFoundError(task_id=task_id) from None

    def get_all_running_tasks(self) -> list[AgentTaskModel]:
        return list(self._running_tasks)

    def get_running_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        try:
            return self._running_tasks[task_id]
        except KeyError:
            raise AgentTaskNotFoundError(task_id=task_id) from None

    def get_all_completed_tasks(self) -> list[AgentTaskModel]:
        return list(self._completed_tasks)

    def get_completed_task_by_task_id(self, task_id: str) -> AgentTaskModel:
        try:
            return self._completed_tasks[task_id]
        except KeyError:
            raise AgentTaskNotFoundError(task_id=task_id) from None

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
            raise AgentTaskNotFoundError(task_id=task_id) from None

    async def add_result_message(self, result_message: AgentResultMessageModel) -> None:
        if str(result_message.task_id) not in self._running_tasks:
            raise AgentResultHasNoCorrespondingTaskError(
                result_id=str(result_message.result_id),
                corresponding_task_id=str(result_message.task_id),
                agent_str=str(self),
            )

        agent_capability = self._running_agent_capabilities[str(result_message.task_id)]
        await agent_capability.result_messages_queue.put(result_message)

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
            raise AgentResultIDNotFoundError(result_id=result_id) from None

    def to_json(self) -> dict:
        return {
            "agent_id": str(self.agent_id),
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "agent_type": self.agent_type.to_json() if self.agent_type else None,
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

    def _move_queued_task_to_running(self, task_id: str) -> None:
        task = self._queued_tasks.pop(task_id)
        task.state = AgentTaskState.RUNNING
        self._running_tasks[str(task.task_id)] = task

    def _move_running_task_to_completed(self, task_id: str) -> None:
        task = self._running_tasks.pop(task_id)
        task.state = AgentTaskState.COMPLETED
        self._completed_tasks[str(task.task_id)] = task

    async def _start_agent_capability(
        self,
        agent_capability: type[BaseAgentCapability],
        task_message: AgentTaskMessageModel,
    ) -> None:
        async def _agent_capability_task_handler(
            agent_capability: BaseAgentCapability,
            task_message: AgentTaskMessageModel,
        ):
            if agent_capability.is_atomic:
                async with self._task_messages_queue_lock:
                    result_message = await agent_capability.execute(
                        task_message=task_message,
                    )
            else:
                # "Wait" for the lock to be released but dont actually hold it while
                # executing the agent capability. This allows non-atomic agent
                # capabilities to interleave their task messages with other agent
                # capabilities.
                async with self._task_messages_queue_lock:
                    pass
                result_message = await agent_capability.execute(
                    task_message=task_message,
                )

            if not isinstance(result_message, AgentResultMessageModel):
                # TODO: Tidy this up to use a custom exception type.
                raise TypeError(
                    f"Agent capability '{agent_capability.name}' returned an "
                    f"invalid result message type '{type(result_message)}'. Expected "
                    f"'{AgentResultMessageModel.__name__}'.",
                )

            # Upon receiving the final aggregated result message we can remove the
            # agent capability as it is now no longer considered to be running.
            self._running_agent_capabilities.pop(str(task_message.task_id))

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
            task_messages_queue=self._task_messages_queue,
        )
        self._running_agent_capabilities[str(task_message.task_id)] = (
            running_agent_capability
        )

        agent_capability_task = asyncio.create_task(
            _agent_capability_task_handler(
                agent_capability=running_agent_capability,
                task_message=task_message,
            ),
        )
        self._agent_capability_tasks.add(agent_capability_task)
        # Once the task is finished we have it automatically remove its own reference
        # within the set to avoid holding references to finished tasks indefinitely.
        agent_capability_task.add_done_callback(self._agent_capability_tasks.discard)
