import asyncio
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any, get_type_hints

from loguru import logger
from pydantic import UUID4, BaseModel, JsonValue, ValidationError

from consortium.framework._components import State
from consortium.framework.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents import BaseAgentCapability
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.event_hooks import EventType
from consortium.framework.exceptions.agent_capabilties_framework_exception import (
    AgentCapabilityRuntimeError as AgentCapabilityRuntimeFrameworkError,
)
from consortium.framework.listeners import BaseListener
from consortium.server import server_singletons as server_singletons
from consortium.server.exceptions.consortium_exceptions.agent_capabilities_consortium_exceptions import (
    AgentCapabilityRuntimeError,
)
from consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions import (
    AgentCapabilityNotFoundError,
    AgentCapabilityOptionNotFoundError,
    AgentCapabilityOptionValueValidationError,
    AgentCreationParameterTypeError,
    AgentResultHasNoCorrespondingTaskError,
    AgentTaskNotFoundError,
    AgentTypeResolutionError,
    MissingRequiredAgentCapabilityOptionError,
)
from consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions import (
    AgentTypeNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions import (
    ListenerNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions import (
    PayloadNotFoundError,
)
from consortium.server.models.agent_task_models import AgentTaskEventType
from consortium.server.objects.agent_task_objects import AgentTask, AgentTaskState
from consortium.server.server_logging import LoggerType
from consortium.server.services.agent_file_manager_service import (
    AgentFileManagerService,
)
from consortium.server.utils import generate_random_human_readable_name, normalize_uuid


class AgentStatus(StrEnum):
    # Capabilities are responsible for marking agents as ACTIVE or INACTIVE based on
    # whether the agent is connected or not. An agent can only be marked as ACTIVE or
    # INACTIVE for a listener that is currently running.
    ACTIVE = "ACTIVE"  # Running normally, attached to running listener
    INACTIVE = "INACTIVE"  # Agent was told explicitly to go inactive or lost connection

    # ORPHANED and UNREACHABLE are states inferred from the state of the attached
    # listener of an agent, the framework manages these states.
    ORPHANED = "ORPHANED"  # Attached listener temporarily not running but not deleted. For example, ERRORED or STOPPED
    UNREACHABLE = "UNREACHABLE"  # Attached listener was explicitly deleted, even if a new listener is created with the same parameters it will not recognize that agent


class _AgentParametersModel(BaseModel):
    listener_id: UUID4
    payload_id: UUID4 | None
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
        listener_id: str | uuid.UUID,
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
                listener_id=listener_id,
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
                parameter_name=str(exc.errors()[0]["loc"][0]),
                parameter_type=get_type_hints(_AgentParametersModel)[
                    exc.errors()[0]["loc"][0]
                ],
            ) from None

        # Check if the provided listener ID corresponds to an existing listener. This
        # will raise `ListenerNotFoundError` if it does not.
        server_singletons.listeners_service.get_listener_by_listener_id(
            listener_id=listener_id
        )
        # Store the listener ID privately we reference the listener via a property to
        # always get the latest state of the listener.
        self._listener_id = listener_id

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

        # By default, agents are considered ACTIVE when created. `self._status` is used
        # to track the reported status of the agent while the framework may
        # automatically infer other statuses such as ORPHANED or UNREACHABLE based on
        # the state of the attached listener. Even if an agent was marked as ACTIVE or
        # INACTIVE by the listener, the moment it is not running or deleted, the agent
        # state will be ORPHANED or UNREACHABLE respectively.
        self._status = AgentStatus.ACTIVE
        # TODO: Move all the tasks to a database instead of storing them in memory.
        self._tasks = {}
        self._task_messages_queue = asyncio.Queue()
        self._agent_capability_execution_lock = asyncio.Lock()
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

    @property
    def connected_listener(self) -> BaseListener | None:
        if self._listener_id is None:
            return None

        try:
            return server_singletons.listeners_service.get_listener_by_listener_id(
                listener_id=self._listener_id
            )
        except ListenerNotFoundError:
            # Listener was deleted, clear the reference to prevent repeated querying
            # of the non-existent listener.
            self._listener_id = None
            return None

    @property
    def status(self) -> AgentStatus:
        if self._listener_id is None:
            return AgentStatus.UNREACHABLE

        try:
            listener = server_singletons.listeners_service.get_listener_by_listener_id(
                listener_id=self._listener_id
            )
        except ListenerNotFoundError:
            # Listener was deleted, clear the reference to prevent repeated querying
            # of the non-existent listener.
            self._listener_id = None
            return AgentStatus.UNREACHABLE

        if listener.status.state != State.RUNNING:
            # When the listener is not running we consider the agent to be ORPHANED.
            # When the listener comes back online the agent is considered INACTIVE until
            # the listener explicitly marks it as ACTIVE again OR the agent checks in
            # again at which point the `agents_service.check_in_agent_by_agent_id`
            # method will mark the agent as ACTIVE again.
            self._status = AgentStatus.INACTIVE
            return AgentStatus.ORPHANED

        return self._status

    async def submit_task(self, task: AgentTask) -> None:
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

        self._tasks[str(task.task_id)] = task

        await self._start_agent_capability(
            agent_capability=agent_capability,
            task=task,
        )

    async def send_task_message(
        self, task_message: TaskLaunchMessageModel, timeout: float | None = None
    ) -> None:
        if timeout is None:
            await self._task_messages_queue.put(task_message)
        else:
            await asyncio.wait_for(
                self._task_messages_queue.put(task_message),
                timeout=timeout,
            )

    async def get_next_task_message(
        self, timeout: float | None = None
    ) -> TaskLaunchMessageModel | None:
        try:
            if timeout == 0:
                message = self._task_messages_queue.get_nowait()
            elif timeout is None:
                message = await self._task_messages_queue.get()
            else:
                message = await asyncio.wait_for(
                    self._task_messages_queue.get(), timeout
                )

            # A task may emit one or more task messages. The first time a task message
            # is fetched for a task we mark the task as running if it is not already
            # running.
            task = self.get_task_by_task_id(task_id=message.task_id)
            if task.status.state != AgentTaskState.RUNNING:
                task.status.state = AgentTaskState.RUNNING
                task.datetime_started = datetime.now()
            return message
        except asyncio.QueueEmpty:
            return None
        except TimeoutError:
            return None

    def get_all_tasks(
        self,
        state: AgentTaskState | None = None,
    ) -> list[AgentTask]:
        if state is not None:
            return [task for task in self._tasks.values() if task.status.state == state]
        return list(self._tasks.values())

    def get_all_queued_tasks(self) -> list[AgentTask]:
        return self.get_all_tasks(state=AgentTaskState.QUEUED)

    def get_all_running_tasks(self) -> list[AgentTask]:
        return self.get_all_tasks(state=AgentTaskState.RUNNING)

    def get_all_succeeded_tasks(self) -> list[AgentTask]:
        return self.get_all_tasks(state=AgentTaskState.SUCCEEDED)

    def get_all_failed_tasks(self) -> list[AgentTask]:
        return self.get_all_tasks(state=AgentTaskState.FAILED)

    def get_all_errored_tasks(self) -> list[AgentTask]:
        return self.get_all_tasks(state=AgentTaskState.ERRORED)

    def get_task_by_task_id(
        self,
        task_id: str | uuid.UUID,
        state: AgentTaskState | None = None,
    ) -> AgentTask:
        task_id = normalize_uuid(value=task_id)

        for task in self.get_all_tasks(state=state):
            if task_id == str(task.task_id):
                return task
        raise AgentTaskNotFoundError(task_id=task_id)

    def get_queued_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTask:
        return self.get_task_by_task_id(task_id=task_id, state=AgentTaskState.QUEUED)

    def get_running_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTask:
        return self.get_task_by_task_id(task_id=task_id, state=AgentTaskState.RUNNING)

    def get_succeeded_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTask:
        return self.get_task_by_task_id(task_id=task_id, state=AgentTaskState.SUCCEEDED)

    def get_failed_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTask:
        return self.get_task_by_task_id(task_id=task_id, state=AgentTaskState.FAILED)

    def get_errored_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTask:
        return self.get_task_by_task_id(task_id=task_id, state=AgentTaskState.ERRORED)

    def delete_queued_task_by_task_id(self, task_id: str | uuid.UUID) -> None:
        try:
            task = self.get_queued_task_by_task_id(task_id=task_id)
            if task.status.state != AgentTaskState.QUEUED:
                raise AgentTaskNotFoundError(task_id=str(task_id))
            del self._tasks[str(task.task_id)]
        except KeyError:
            raise AgentTaskNotFoundError(task_id=str(task_id)) from None

    async def dispatch_task_output_message(
        self, task_output_message: TaskOutputMessageModel
    ) -> None:
        try:
            task = self.get_task_by_task_id(task_id=task_output_message.task_id)
        except AgentTaskNotFoundError:
            raise AgentResultHasNoCorrespondingTaskError(
                corresponding_task_id=str(task_output_message.task_id),
                agent_str=str(self),
            ) from None

        if task.status.state != AgentTaskState.RUNNING:
            self.logger.warning(
                "Agent received a result for task {} that does exist with status {} but "
                "is not currently running.",
                task,
                task.status,
            )
            # TODO: Possibly make this error different to differentiate the error conditions
            raise AgentResultHasNoCorrespondingTaskError(
                corresponding_task_id=str(task_output_message.task_id),
                agent_str=str(self),
            )

        agent_capability = self._running_agent_capabilities[
            str(task_output_message.task_id)
        ]
        await agent_capability.result_messages_queue.put(task_output_message)

    def mark_as_active(self) -> None:
        self._status = AgentStatus.ACTIVE

    def mark_as_inactive(self) -> None:
        self._status = AgentStatus.INACTIVE

    def to_json(self) -> dict:
        connected_listener = self.connected_listener
        if connected_listener:
            connected_listener_json = connected_listener.to_json_reference()
        else:
            connected_listener_json = None

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
            "status": self.status,
            "connected_listener": connected_listener_json,
            "agent_data": self.agent_data,
        }

    def to_json_reference(self) -> dict[str, str]:
        return {
            "agent_id": str(self.agent_id),
            "name": self.name,
        }

    async def _start_agent_capability(
        self,
        agent_capability: type[BaseAgentCapability],
        task: AgentTask,
    ) -> None:
        async def _agent_capability_task_handler(
            agent_capability: BaseAgentCapability,
            task: AgentTask,
        ):
            # Strip redundant information from the task to create the initial task
            # message
            task_message = TaskLaunchMessageModel(
                task_id=task.task_id,
                command=task.command,
                arguments=task.arguments,
            )
            try:
                if agent_capability.is_atomic:
                    async with self._agent_capability_execution_lock:
                        task_outcome = await agent_capability.execute(
                            task_message=task_message
                        )
                else:
                    # "Wait" for the lock to be released but dont actually hold it while
                    # executing the agent capability. This allows non-atomic agent
                    # capabilities to interleave their task messages with other agent
                    # capabilities.
                    async with self._agent_capability_execution_lock:
                        pass

                    task_outcome = await agent_capability.execute(
                        task_message=task_message
                    )

                # Upon returning without raising an error check the `task_outcome` to
                # see if it is present or not and emit the final event based on that
                if isinstance(task_outcome, Success):
                    task.status._transition_to_succeeded()
                    task.append_event(
                        event_type=AgentTaskEventType.SUCCESS,
                        message=task_outcome.task_output_message.message,
                        data=task_outcome.task_output_message.data,
                    )
                elif isinstance(task_outcome, Failure):
                    # TODO: Decide on a standard way for Failure to communicate message
                    #  and data as compared to `AgentCapabilityRuntimeFrameworkError`
                    task.status._transition_to_failed()
                    task.append_event(
                        event_type=AgentTaskEventType.FAILURE,
                        message=task_outcome.task_output_message.message,
                        data=task_outcome.task_output_message.data,
                    )
                elif task_outcome is None:
                    pass
                else:
                    self.logger.warning(
                        "Agent {} had a task {} that completed but returned a value "
                        "that was `{!r}` instead of `Success`, `Failure` or `None`. "
                        "This return value was ignored but should be fixed.",
                        self,
                        task,
                        task_outcome,
                    )
            except AgentCapabilityRuntimeFrameworkError as exc:
                task.status._transition_to_failed(error=exc)
                # TODO: Decide on what to append in this case and how data should be
                #  communicated via `AgentCapabilityRuntimeFrameworkError` and where
                #  the exception should live
                task.append_event(
                    event_type=AgentTaskEventType.FAILURE,
                    message=exc.message,
                    data={
                        "detail": exc.detail,
                    },
                )
            except Exception as exc:
                self.logger.error(
                    "Failed to execute agent capability '{}'. An unhandled "
                    "exception was raised during execution. {}: {}",
                    str(agent_capability),
                    exc.__class__.__name__,
                    str(exc),
                )
                task.status._transition_to_errored(
                    error=AgentCapabilityRuntimeError(
                        agent_capability_name=agent_capability.name,
                        error_message=(
                            "An unhandled exception was raised during execution. "
                            f"{exc.__class__.__name__}: {exc}"
                        ),
                    )
                )
                # TODO: Decide on what to append in this case
                task.append_event(
                    event_type=AgentTaskEventType.FAILURE,
                    message=str(exc),
                )

            # Upon receiving the final aggregated result message we can remove the
            # agent capability as it is now no longer considered to be running.
            self._running_agent_capabilities.pop(str(task_message.task_id))

            # Finally we fire the event to notify all event handlers that a task has
            # completed
            await server_singletons.events_service.trigger_event(
                event_type=EventType.AGENT_TASK_COMPLETED,
                message=(
                    f"Agent {self} completed task {task} with status {task.status}"
                ),
                data={
                    "agent_id": str(self.agent_id),
                    "task": task.to_json(),
                },
            )

        running_agent_capability = agent_capability(agent=self, task=task)
        self._running_agent_capabilities[str(task.task_id)] = running_agent_capability

        agent_capability_task = asyncio.create_task(
            _agent_capability_task_handler(
                agent_capability=running_agent_capability,
                task=task,
            ),
        )
        self._agent_capability_tasks.add(agent_capability_task)
        # Once the task is finished we have it automatically remove its own reference
        # within the set to avoid holding references to finished tasks indefinitely.
        agent_capability_task.add_done_callback(self._agent_capability_tasks.discard)
