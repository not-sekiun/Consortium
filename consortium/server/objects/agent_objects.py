import asyncio
import uuid
from datetime import datetime
from typing import Any, get_type_hints

from loguru import logger
from pydantic import BaseModel, JsonValue, ValidationError

from consortium.framework.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.agents import BaseAgentCapability
from consortium.framework.event_hooks import EventType
from consortium.server import server_singletons as server_singletons
from consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions import (
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
from consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions import (
    AgentTypeNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions import (
    PayloadNotFoundError,
)
from consortium.server.models.agent_models import (
    AgentResultModel,
    AgentResultStatus,
    AgentTaskModel,
    AgentTaskStatus,
)
from consortium.server.server_logging import LoggerType
from consortium.server.services.agent_file_manager_service import (
    AgentFileManagerService,
)
from consortium.server.utils import generate_random_human_readable_name, normalize_uuid


class _AgentParametersModel(BaseModel):
    payload_id: str | uuid.UUID | None
    agent_type: str | None
    name: str | None
    description: str
    endpoint: str
    user: str | None
    is_admin: bool | None
    os: str | None
    version: str | None
    arch: str | None
    pid: int | None
    locale: str | None
    remote_host_address: str | None
    local_host_address: str | None
    hostname: str | None
    agent_data: dict[str, JsonValue]


class Agent:
    def __init__(
        self,
        payload_id: str | uuid.UUID | None = None,
        agent_type: str | None = None,
        name: str | None = None,
        description: str = "",
        endpoint: str = "",
        user: str | None = None,
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
                user=user,
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
            raise AgentTypeResolutionError._due_to_no_identifier_provided()
        # Attempt to resolve the agent type via the payload ID if one was provided.
        if payload_id is not None:
            payload_id = normalize_uuid(value=payload_id)

            try:
                payload = server_singletons.payloads_service.get_payload_by_payload_id(
                    payload_id=payload_id
                )
                self.agent_type = payload.agent_type
            except PayloadNotFoundError:
                raise AgentTypeResolutionError._due_to_payload_not_found_error(
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
                raise AgentTypeResolutionError._due_to_agent_type_not_found_error(
                    agent_type_name=agent_type,
                ) from None

        self.payload_id = payload_id
        self.name = generate_random_human_readable_name() if name is None else name
        self.description = description
        self.endpoint = endpoint
        self.user = user
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

        self.agent_file_manager_service = AgentFileManagerService(agent=self)
        self.logger = logger.bind(
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
            f"user={self.user!r}, "
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

    async def submit_task(self, task: AgentTaskModel) -> None:
        if task.command not in self.agent_type.agent_capabilities:
            raise AgentCapabilityNotFoundError(
                command=task.command,
                agent_str=str(self),
                agent_type_str=str(self.agent_type),
            )

        agent_capability = self.agent_type.agent_capabilities[task.command]

        # Fill in default option values for options that were not provided in the
        # arguments dictionary. For options that do not have a default value
        # they fill in as `None`
        for option_name, option in agent_capability.options.items():
            if option_name not in task.arguments:
                task.arguments[option_name] = option.default_value

        # Validate entire constructed argument set.
        for option_name, value in task.arguments.items():
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
            if option.required and option_name not in task.arguments:
                raise MissingRequiredAgentCapabilityOptionError(
                    agent_str=str(self),
                    agent_capability_name=agent_capability.name,
                    option_name=option_name,
                )

        # TODO: Handle validation failure here.
        # Run validation function on the entire set of arguments if one was provided.
        if agent_capability.validating_function:
            agent_capability.validating_function(task.arguments)

        self._queued_tasks[str(task.task_id)] = task

        await self._start_agent_capability(
            agent_capability=agent_capability,
            task=task,
        )

    async def get_next_task_message(
        self, timeout: float | None = None
    ) -> AgentTaskMessageModel | None:
        try:
            if timeout == 0:
                message = self._task_messages_queue.get_nowait()
            elif timeout is None:
                message = await self._task_messages_queue.get()
            else:
                message = await asyncio.wait_for(
                    self._task_messages_queue.get(), timeout
                )

            if str(message.task_id) in self._queued_tasks:
                self._move_queued_task_to_running(task_id=str(message.task_id))
            return message
        except asyncio.QueueEmpty:
            return None
        except TimeoutError:
            return None

    def get_all_tasks(
        self,
        status: AgentTaskStatus | None = None,
    ) -> list[AgentTaskModel]:
        if status == AgentTaskStatus.QUEUED:
            return list(self._queued_tasks.values())
        elif status == AgentTaskStatus.RUNNING:
            return list(self._running_tasks.values())
        elif status == AgentTaskStatus.COMPLETED:
            return list(self._completed_tasks.values())
        else:
            return [
                *self._queued_tasks.values(),
                *self._running_tasks.values(),
                *self._completed_tasks.values(),
            ]

    def get_all_queued_tasks(self) -> list[AgentTaskModel]:
        return self.get_all_tasks(status=AgentTaskStatus.QUEUED)

    def get_all_running_tasks(self) -> list[AgentTaskModel]:
        return self.get_all_tasks(status=AgentTaskStatus.RUNNING)

    def get_all_completed_tasks(self) -> list[AgentTaskModel]:
        return self.get_all_tasks(status=AgentTaskStatus.COMPLETED)

    def get_task_by_task_id(
        self,
        task_id: str | uuid.UUID,
        status: AgentTaskStatus | None = None,
    ) -> AgentTaskModel:
        task_id = normalize_uuid(value=task_id)

        for task in self.get_all_tasks(status=status):
            if task_id == str(task.task_id):
                return task
        raise AgentTaskNotFoundError(task_id=task_id)

    def get_queued_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTaskModel:
        return self.get_task_by_task_id(task_id=task_id, status=AgentTaskStatus.QUEUED)

    def get_running_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTaskModel:
        return self.get_task_by_task_id(task_id=task_id, status=AgentTaskStatus.RUNNING)

    def get_completed_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTaskModel:
        return self.get_task_by_task_id(
            task_id=task_id, status=AgentTaskStatus.COMPLETED
        )

    def delete_queued_task_by_task_id(self, task_id: str | uuid.UUID) -> None:
        task_id = normalize_uuid(value=task_id)

        try:
            self._queued_tasks.pop(task_id)
        except KeyError:
            raise AgentTaskNotFoundError(task_id=task_id) from None

    # TODO: Make the service submit result messages so users dont call low level
    #  framework methods
    async def submit_result_message(
        self, result_message: AgentResultMessageModel
    ) -> None:
        if str(result_message.task_id) not in self._running_tasks:
            raise AgentResultHasNoCorrespondingTaskError(
                corresponding_task_id=str(result_message.task_id),
                agent_str=str(self),
            )

        agent_capability = self._running_agent_capabilities[str(result_message.task_id)]
        await agent_capability.result_messages_queue.put(result_message)

    def get_all_results(
        self,
        status: AgentResultStatus | None = None,
    ) -> list[AgentResultModel]:
        if status is not None:
            return [
                result for result in self._results.values() if result.status == status
            ]
        return list(self._results.values())

    def get_all_successful_results(self) -> list[AgentResultModel]:
        return self.get_all_results(status=AgentResultStatus.SUCCESS)

    def get_all_failed_results(self) -> list[AgentResultModel]:
        return self.get_all_results(status=AgentResultStatus.FAILURE)

    def get_all_errored_results(self) -> list[AgentResultModel]:
        return self.get_all_results(status=AgentResultStatus.ERROR)

    def get_result_by_task_id(self, task_id: str | uuid.UUID) -> AgentResultModel:
        task_id = normalize_uuid(value=task_id)

        for result in self._results.values():
            if result.task_id == task_id:
                return result
        raise AgentResultTaskIDNotFoundError(task_id=task_id)

    def get_result_by_result_id(self, result_id: str | uuid.UUID) -> AgentResultModel:
        result_id = normalize_uuid(value=result_id)

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
            "user": self.user,
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
        task.status = AgentTaskStatus.RUNNING
        self._running_tasks[str(task.task_id)] = task

    def _move_task_to_completed(self, task_id: str) -> None:
        # The task can still be queued if the agent didn't fetch the task message
        # before the capability timed out (if it specified a finite timeout). In this
        # case we move it from queued to completed.
        if task_id in self._queued_tasks:
            task = self._queued_tasks.pop(task_id)
        # This is the normal case where the task is running and is now completed.
        elif task_id in self._running_tasks:
            task = self._running_tasks.pop(task_id)
        else:
            raise AssertionError(
                f"Task with task ID '{task_id}' not found when moving from the queued "
                f"or running dictionary to completed."
            )
        task.status = AgentTaskStatus.COMPLETED
        self._completed_tasks[str(task.task_id)] = task

    async def _start_agent_capability(
        self,
        agent_capability: type[BaseAgentCapability],
        task: AgentTaskMessageModel,
    ) -> None:
        async def _agent_capability_task_handler(
            agent_capability: BaseAgentCapability,
            task_message: AgentTaskMessageModel,
        ):
            try:
                if agent_capability.is_atomic:
                    async with self._task_messages_queue_lock:
                        result_message = await agent_capability.execute(
                            agent=self,
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
                        agent=self,
                        task_message=task_message,
                    )

                if not isinstance(result_message, AgentResultMessageModel):
                    self.logger.error(
                        "Agent capability '{}' returned an invalid type '{}'. "
                        "Expected `AgentResultMessageModel` to be returned.",
                        agent_capability.name,
                        type(result_message),
                    )
                    result = AgentResultModel(
                        status=AgentResultStatus.ERROR,
                        message=(
                            f"Failed to execute agent capability "
                            f"'{agent_capability.name}'. Agent capability returned an "
                            f"invalid type '{type(result_message)}'. "
                            f"Expected `AgentResultMessageModel` to be returned."
                        ),
                        task_id=task_message.task_id,
                        command=task_message.command,
                        arguments=task_message.arguments,
                        datetime_started=task.datetime_started,
                    )
                else:
                    result = AgentResultModel(
                        status=AgentResultStatus.SUCCESS
                        if result_message.success
                        else AgentResultStatus.FAILURE,
                        message=result_message.message,
                        data=result_message.data,
                        task_id=task_message.task_id,
                        command=task_message.command,
                        arguments=task_message.arguments,
                        datetime_started=task.datetime_started,
                    )
            except Exception as exc:
                self.logger.error(
                    "Failed to execute agent capability '{}' due to an unhandled "
                    "exception raised during execution. {}: {}",
                    agent_capability.name,
                    exc.__class__.__name__,
                    str(exc),
                )
                result = AgentResultModel(
                    status=AgentResultStatus.ERROR,
                    message=(
                        f"Failed to execute agent capability '{agent_capability.name}' "
                        f"due to an unhandled exception raised during execution. "
                        f"{exc.__class__.__name__}: {str(exc)}"
                    ),
                    task_id=task_message.task_id,
                    command=task_message.command,
                    arguments=task_message.arguments,
                    datetime_started=task.datetime_started,
                )

            # Upon receiving the final aggregated result message we can remove the
            # agent capability as it is now no longer considered to be running.
            self._running_agent_capabilities.pop(str(task_message.task_id))

            self._results[str(result.result_id)] = result

            # Adding the result implies that the task is completed so we can now
            # move the task from the running tasks to the completed tasks.
            self._move_task_to_completed(
                task_id=str(result_message.task_id),
            )

            # Finally we fire the event to notify all event handlers that a result
            # has been received.
            await self._events_service.trigger_event(
                event_type=EventType.AGENT_RESULT_RECEIVED,
                message=(
                    f"Agent {self} received result with result ID {result.result_id} "
                    f"for task with task ID {task_message.task_id}"
                ),
                data={
                    "agent_id": str(self.agent_id),
                    "result": result.model_dump(mode="json"),
                },
            )

        running_agent_capability = agent_capability(
            task_messages_queue=self._task_messages_queue,
        )
        self._running_agent_capabilities[str(task.task_id)] = running_agent_capability

        # Strip redundant information from the task to create the initial task message
        task_message = AgentTaskMessageModel(
            task_id=task.task_id,
            command=task.command,
            arguments=task.arguments,
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
