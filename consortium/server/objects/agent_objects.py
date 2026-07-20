import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from enum import StrEnum
from typing import Any, get_type_hints

from loguru import logger
from pydantic import UUID4, BaseModel, JsonValue, ValidationError

from consortium.framework._core.components import State
from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCapabilityExecutionError,
    AgentCapabilityLaunchError,
)
from consortium.framework._core.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework._core.task_messages_queue import TaskMessagesQueue
from consortium.framework.agents import BaseAgentCapability, TaskInputMessageModel
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.event_hooks import EventType
from consortium.framework.listeners import BaseListener
from consortium.framework.signal_exceptions.agent_capabilties_signal_exception import (
    AgentCapabilityExecutionError as AgentCapabilityExecutionSignal,
    AgentCapabilityLaunchError as AgentCapabilityLaunchSignal,
)
from consortium.server import server_singletons as server_singletons
from consortium.server.exceptions.object_exceptions.agent_object_exceptions import (
    AgentCapabilityNotFoundError,
    AgentCapabilityOptionNotFoundError,
    AgentCapabilityOptionValueValidationError,
    AgentCreationParameterTypeError,
    AgentTaskNotFoundError,
    AgentTypeResolutionError,
    MissingRequiredAgentCapabilityOptionError,
)
from consortium.server.exceptions.service_exceptions.c2_types_service_exceptions import (
    AgentTypeNotFoundError,
)
from consortium.server.exceptions.service_exceptions.listeners_service_exceptions import (
    ListenerNotFoundError,
)
from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    ResourceNotFoundError,
)
from consortium.server.models.agent_task_models import AgentTaskEventType
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.agent_task_objects import AgentTask, AgentTaskState
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
    remote_ip: str | None
    local_ip: str | None
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
        remote_ip: str | None = None,
        local_ip: str | None = None,
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
                remote_ip=remote_ip,
                local_ip=local_ip,
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
                payload = server_singletons.payloads_service.get_payload_by_resource_id(
                    resource_id=payload_id
                )
                self.agent_type = payload.agent_type
            except ResourceNotFoundError:
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
        self.remote_ip = remote_ip
        self.local_ip = local_ip
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

        # Fired when a new task is started (specifically after its outbox is added to
        # self._task_outboxes). This is used specifically and only to wake up
        # self.get_next_task_message_sequential() when it is called with a timeout of
        # `None` while there are no readable outboxes since it will block indefinitely
        # until the first valid task message can be pulled out
        self._new_task_started_event = asyncio.Event()
        # Shared across all of this agent's capability outboxes: every successful put on
        # an outbox notifies this condition. get_next_task_message_any waits on it to be
        # woken the moment any running capability produces a message, then scans the
        # outboxes in insertion order for the first one with a pending message.
        self._outbox_activity = asyncio.Condition()
        # Each running capability's inbox mapped by task ID. Incoming results are routed
        # to the matching capability's inbox by dispatch_task_output_message. An inbox is
        # only useful while the capability is running to receive those results, so an
        # entry lives from capability start to completion. This is the counterpart of
        # self._task_outboxes, which (unlike an inbox) outlives its capability so buffered
        # output stays readable until drained.
        self._task_inboxes: dict[str, TaskMessagesQueue] = {}
        # Each task's outbox mapped by task ID, tracked separately from self._task_inboxes
        # because an outbox outlives its capability: a capability may stream messages and
        # then exit, and those buffered messages must stay readable until drained. An
        # outbox is added when its capability starts and dropped only once it reaches end
        # of stream (shut down and fully drained). This is the set of outboxes the
        # get_next_task_message_* readers work over.
        self._task_outboxes: dict[str, TaskMessagesQueue] = {}
        # Each task's capability handler asyncio task mapped by task ID. Holding the
        # references prevents their garbage collection while running, and the mapping lets
        # us cancel a specific task's handler on deletion.
        self._task_handler_async_tasks: dict[str, asyncio.Task] = {}

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
            f"remote_ip={self.remote_ip!r}, "
            f"local_ip={self.local_ip!r}, "
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

    async def get_next_task_message_by_task_id(
        self,
        task_id: str | uuid.UUID,
        timeout: float | None = None,
    ) -> TaskInputMessageModel | TaskOutputMessageModel | None:
        """Get the next task message produced by the capability for the specified task.

        Reads follow the task's outbox lifecycle, not the capability's: a capability may
        stream messages and then exit, and those buffered messages must remain readable
        until drained. The outbox is tracked until it reaches end of stream (shut down
        and fully drained), at which point it is dropped and this returns None."""
        task = self.get_task_by_task_id(task_id=task_id)

        # The outbox is tracked independently of self._task_inboxes (which only lives
        # while the capability is running to accept results). A missing outbox means it
        # was never produced or has already been fully drained to end of stream.
        outbox = self._task_outboxes.get(str(task.task_id))
        if outbox is None:
            return None

        try:
            task_message = await outbox.get(timeout=timeout)
        except TimeoutError:
            # A timeout means "nothing available yet"; the queue returns `None` on its
            # own for end of stream. We collapse the timeout to `None` here so agent
            # level callers get a single "no message" signal to poll on.
            return None

        if task_message is None:
            # End of stream: the capability finished and the outbox is fully drained, so
            # drop it. Subsequent reads for this task return None.
            self._task_outboxes.pop(str(task.task_id), None)
            return None

        # The launch message is the first thing a capability puts on its outbox. Popping
        # it is the point at which the agent has acknowledged and picked up the task, so
        # transition it from QUEUED to RUNNING. This gate is required because
        # dispatch_task_output_message drops any result for a task that is not RUNNING.
        # It is guarded on QUEUED so a task whose capability already completed (streamed
        # then exited) and is only now being drained is not transitioned.
        if (
            isinstance(task_message, TaskLaunchMessageModel)
            and task.status.state == AgentTaskState.QUEUED
        ):
            task.status._transition_to_running()
            task.datetime_started = datetime.now()

        return task_message

    async def _wait_for_a_readable_outbox(
        self, timeout: float | None
    ) -> tuple[bool, float | None]:
        # Block until there is at least one outbox to read from, returning
        # (ready, remaining_timeout). An outbox is readable while its capability is
        # running and remains readable after the capability exits until its buffered
        # messages are drained, so this waits on tracked outboxes (not running
        # capabilities). `timeout` is the total budget for producing the next message,
        # so the time spent waiting for an outbox to appear is deducted from it and the
        # remainder is handed back for the caller to spend waiting on a message.
        if self._task_outboxes:
            return True, timeout

        # Always reset the event before waiting on it: it may still be set from an
        # earlier task that has since finished and been drained. Without clearing, a
        # stale set would let us fall through with no outboxes to read. This is safe
        # because we only reach here with no tracked outboxes and there is no await
        # between the emptiness check and the clear.
        self._new_task_started_event.clear()

        if timeout is None:
            await self._new_task_started_event.wait()
            return True, None

        start_time = asyncio.get_running_loop().time()
        try:
            await asyncio.wait_for(self._new_task_started_event.wait(), timeout=timeout)
        except TimeoutError:
            return False, 0.0
        remaining = timeout - (asyncio.get_running_loop().time() - start_time)
        return True, max(remaining, 0.0)

    async def get_next_task_message_sequential(
        self, timeout: float | None = None
    ) -> TaskInputMessageModel | TaskOutputMessageModel | None:
        """Get the next task message from the earliest tasked outbox, draining it
        completely (including any messages a streamed-and-exited capability left behind)
        before moving on to the next one."""
        ready, timeout = await self._wait_for_a_readable_outbox(timeout=timeout)
        if not ready:
            return None

        # Dictionaries preserve insertion order, so the first tracked outbox is the
        # earliest tasked one. We drain it completely (its end of stream drops it from
        # self._task_outboxes) before the next call moves on to the following outbox.
        task_id = next(iter(self._task_outboxes))
        return await self.get_next_task_message_by_task_id(
            task_id=task_id, timeout=timeout
        )

    def _first_outbox_with_pending_message(self) -> str | None:
        # Scan tracked outboxes in insertion order and return the task ID of the first
        # one with a message waiting, or None if none do. Insertion order gives a stable,
        # fair-enough policy that favours the earliest tasked capabilities. Outboxes that
        # have reached end of stream (a finished capability, fully drained) are dropped as
        # we pass them so they do not accumulate. `empty()` and the end of stream check
        # are plain reads (no outbox lock), so this is a cheap best-effort probe: an
        # outbox reported as ready may be raced empty by another reader before we pull
        # from it, which the caller handles.
        ended_task_ids: list[str] = []
        found_task_id: str | None = None
        for task_id, outbox in self._task_outboxes.items():
            if not outbox.empty():
                found_task_id = task_id
                break
            if outbox.is_at_end_of_stream():
                ended_task_ids.append(task_id)
        for task_id in ended_task_ids:
            self._task_outboxes.pop(task_id, None)
        return found_task_id

    async def get_next_task_message_any(
        self, timeout: float | None = None
    ) -> TaskLaunchMessageModel | TaskOutputMessageModel | None:
        """Get the first available task message from any tasked outbox.

        Waits across every tracked outbox at once and returns the first available
        message, interleaving (muxing) messages in the order they are produced. A
        capability that streams messages and then exits still has its buffered tail
        drained here, since reads follow the outbox lifecycle, not the capability's.
        `timeout` is the total budget until the next message and spans both waiting for a
        capability to start and waiting for one to produce a message; None waits
        indefinitely and 0 polls without blocking. If every outbox drains to end of
        stream while waiting, it keeps blocking until a new task starts."""
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        # Outer loop: repeats only if the outbox we picked was raced empty (or drained to
        # end of stream) between scanning and pulling, in which case we wait again.
        while True:
            task_id: str | None = None

            # Wait for any outbox to have a message. The shared _outbox_activity
            # condition is notified on every successful outbox put, so a wake means some
            # outbox may now be readable. A finished outbox with no buffered messages
            # produces no notify and is skipped (and pruned) by the scan, so once every
            # outbox has drained to end of stream we block here until a newly started
            # task produces its first message.
            async with self._outbox_activity:
                while True:
                    task_id = self._first_outbox_with_pending_message()
                    if task_id is not None:
                        break
                    remaining = None if deadline is None else deadline - loop.time()
                    if remaining is not None and remaining <= 0:
                        return None
                    try:
                        await asyncio.wait_for(self._outbox_activity.wait(), remaining)
                    except TimeoutError:
                        return None

            # The activity lock is released before reading so it is never held while
            # touching an outbox. The outbox likewise notifies the activity condition
            # only after releasing its own lock, so the two locks are never held at the
            # same time by anyone and no lock ordering cycle can form. A non-blocking
            # read cannot deadlock here regardless.
            task_message = await self.get_next_task_message_by_task_id(
                task_id=task_id, timeout=0
            )
            if task_message is not None:
                return task_message
            # The message was taken by another reader or the outbox drained to end of
            # stream between the scan and the read. Loop and wait for the next one.

    async def drain_task_messages_by_task_id(
        self, task_id: str | uuid.UUID
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Infinitely loop and drain task messages from a task until it completes"""
        while True:
            task_message = await self.get_next_task_message_by_task_id(
                task_id=task_id, timeout=None
            )
            if task_message is None:
                break
            yield task_message

    async def drain_task_messages_sequential(
        self,
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Infinitely loop and drain task messages from the earliest running agent
        capability until it completes, then drain the next one and so on."""
        while True:
            task_message = await self.get_next_task_message_sequential(timeout=None)
            if task_message is None:
                continue
            yield task_message

    async def drain_task_messages_any(
        self,
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Infinitely loop and drain task messages from any running agent in the order
        of their availability"""
        while True:
            task_message = await self.get_next_task_message_any(timeout=None)
            if task_message is None:
                continue
            yield task_message

    async def dispatch_task_output_message(
        self, task_output_message: TaskOutputMessageModel
    ) -> bool:
        task_id = str(task_output_message.task_id)

        # Results can legitimately arrive late: the task may have completed, timed out or
        # been deleted between being tasked and the agent posting its result. These are
        # benign lifecycle races, not caller errors, so we drop the stale result and log
        # it rather than raising and pushing the burden of an unrecoverable condition
        # onto the caller and ultimately the remote agent.
        try:
            task = self.get_task_by_task_id(task_id=task_output_message.task_id)
        except AgentTaskNotFoundError:
            self.logger.warning(
                "Agent {} received a task output message for task '{}' that does not "
                "exist (it may have been deleted). The message was dropped.",
                self,
                task_id,
            )
            return False

        if task.status.state != AgentTaskState.RUNNING:
            self.logger.warning(
                "Agent {} received a task output message for task {} with status {} "
                "that is not running. The message was dropped.",
                self,
                task,
                task.status,
            )
            return False

        # A running task should always have a live inbox tracked for it. If it does not
        # the capability finished or was torn down concurrently, drop and log rather than
        # dereferencing a missing entry out of the dispatch path.
        inbox = self._task_inboxes.get(task_id)
        if inbox is None:
            self.logger.warning(
                "Agent {} received a task output message for a running task {} but no "
                "inbox is tracked for it. The message was dropped.",
                self,
                task,
            )
            return False

        try:
            await inbox.put(task_message=task_output_message)
            return True
        except asyncio.QueueShutDown:
            self.logger.warning(
                "Agent {} received a task output message for a running task {} but its "
                "capabilities inbox was marked as shutting down. The message was "
                "dropped.",
                self,
                task,
            )
            return False

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

    async def _discard_task_runtime(self, task_id: str) -> None:
        # Tear down everything a task might still surface so that once it is deleted there
        # is nothing to report for it ever again.
        task_id = str(task_id)

        # Cancel the capability handler so it stops producing and does not fire its
        # completion event. Cancellation raises CancelledError (a BaseException), which
        # slips past the handler's `except Exception`, skipping the terminal transitions
        # and the AGENT_TASK_COMPLETED event.
        handler_task = self._task_handler_async_tasks.pop(task_id, None)
        if handler_task is not None:
            handler_task.cancel()

        # Discard the inbox and outbox. Immediate shutdown drops any buffered messages and
        # wakes a reader already blocked in get() so it sees end of stream (None) rather
        # than the deleted task's messages. Removing them from the maps stops any new
        # reader from picking them up.
        inbox = self._task_inboxes.pop(task_id, None)
        if inbox is not None:
            await inbox.shutdown(immediate=True)
        outbox = self._task_outboxes.pop(task_id, None)
        if outbox is not None:
            await outbox.shutdown(immediate=True)

    async def delete_queued_task_by_task_id(self, task_id: str | uuid.UUID) -> None:
        try:
            task = self.get_queued_task_by_task_id(task_id=task_id)
            if task.status.state != AgentTaskState.QUEUED:
                raise AgentTaskNotFoundError(task_id=str(task_id))
            await self._discard_task_runtime(str(task.task_id))
            del self._tasks[str(task.task_id)]
        except KeyError:
            raise AgentTaskNotFoundError(task_id=str(task_id)) from None

    def mark_as_active(self) -> None:
        self._status = AgentStatus.ACTIVE

    def mark_as_inactive(self) -> None:
        self._status = AgentStatus.INACTIVE

    def to_json(self) -> dict[str, JsonValue]:
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
            "remote_ip": self.remote_ip,
            "local_ip": self.local_ip,
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
            task_launch_message = TaskLaunchMessageModel(
                task_id=task.task_id,
                command=task.command,
                arguments=task.arguments,
            )
            try:
                task_outcome = await agent_capability.execute(
                    task_launch_message=task_launch_message
                )

                # Upon returning without raising an error check the `task_outcome` to
                # see if it is present or not and emit the final event based on that
                if isinstance(task_outcome, Success):
                    # A task reporting Success while still QUEUED means it completed
                    # without the agent ever popping its launch message (never
                    # transitioned through RUNNING). This is allowed for now but is
                    # likely a capability bug, warn so it can be investigated.
                    if task.status.state == AgentTaskState.QUEUED:
                        self.logger.warning(
                            "Agent {} completed task {} to SUCCESS but the task never "
                            "left QUEUED, its launch message was never popped so it was "
                            "never acknowledged by the agent nor transitioned through "
                            "RUNNING.",
                            self,
                            task,
                        )
                    task.status._transition_to_succeeded()
                    task.append_event(
                        event_type=AgentTaskEventType.SUCCESS,
                        message=task_outcome.message,
                        data=task_outcome.data,
                    )
                elif isinstance(task_outcome, Failure):
                    # Failure is the standard deliberate failure path, returned by
                    # on_execute to report a task failure to the operator.
                    task.status._transition_to_failed(
                        error=AgentCapabilityExecutionError(
                            agent_capability_name=agent_capability.name,
                            error_message=task_outcome.message,
                            detail=task_outcome.data,
                        )
                    )
                    task.append_event(
                        event_type=AgentTaskEventType.FAILURE,
                        message=task_outcome.message,
                        data=task_outcome.data,
                    )
                elif task_outcome is None:
                    # None = the capability used the emit-only events pattern and
                    # completed normally without opting in to an explicit outcome. Treat
                    # it as a normal completion: transition to SUCCEEDED without
                    # appending a duplicate terminal event (the capability already
                    # emitted whatever events it wanted via emit_*).
                    if task.status.state == AgentTaskState.QUEUED:
                        self.logger.warning(
                            "Agent {} completed task {} normally but the task never left "
                            "QUEUED, its launch message was never popped so it was never "
                            "acknowledged by the agent nor transitioned through RUNNING.",
                            self,
                            task,
                        )
                    task.status._transition_to_succeeded()
                else:
                    self.logger.warning(
                        "Agent {} had a task {} that completed but returned a value "
                        "that was `{!r}` instead of `Success`, `Failure` or `None`. "
                        "This return value was ignored but should be fixed.",
                        self,
                        task,
                        task_outcome,
                    )
            except AgentCapabilityLaunchSignal as exc:
                # Deliberately raised from on_launch to deny a task from starting, for
                # example when a pre-launch validation check fails. This is the launch
                # (validation) analogue of the execution error below; both are reported
                # as ERRORED but with distinct base messages.
                task.status._transition_to_errored(
                    error=AgentCapabilityLaunchError(
                        agent_capability_name=agent_capability.name,
                        error_message=exc.message,
                        detail=exc.detail,
                    )
                )
                task.append_event(
                    event_type=AgentTaskEventType.FAILURE,
                    message=exc.message,
                    data={"detail": exc.detail},
                )
            except AgentCapabilityExecutionSignal as exc:
                # Deliberately raised from on_execute to stop a running capability with a
                # runtime error. Reported as ERRORED with the execution base message.
                task.status._transition_to_errored(
                    error=AgentCapabilityExecutionError(
                        agent_capability_name=agent_capability.name,
                        error_message=exc.message,
                        detail=exc.detail,
                    )
                )
                task.append_event(
                    event_type=AgentTaskEventType.FAILURE,
                    message=exc.message,
                    data={"detail": exc.detail},
                )
            except Exception as exc:
                # Format the error in the standard `<ErrorClass>: message` form, falling
                # back to just `<ErrorClass>` (no dangling colon) when the exception
                # carries no message, e.g. a bare TimeoutError.
                exception_message = str(exc)
                formatted_exception = (
                    f"{exc.__class__.__name__}: {exception_message}"
                    if exception_message
                    else exc.__class__.__name__
                )
                self.logger.error(
                    "Failed to execute agent capability '{}'. An unhandled "
                    "exception was raised during execution. {}",
                    str(agent_capability),
                    formatted_exception,
                )
                # Guard the terminal transition, this is the last-resort error handler
                # running inside a fire-and-forget asyncio task. If the transition itself
                # raises (for example an illegal state transition) we must swallow and
                # log it rather than let a fresh exception escape the task uncaught.
                try:
                    task.status._transition_to_errored(
                        error=AgentCapabilityExecutionError(
                            agent_capability_name=agent_capability.name,
                            error_message=(
                                "An unhandled exception was raised during execution. "
                                f"{formatted_exception}"
                            ),
                        )
                    )
                    task.append_event(
                        event_type=AgentTaskEventType.FAILURE,
                        message=formatted_exception,
                    )
                except Exception as transition_exc:
                    self.logger.error(
                        "Agent {} failed to transition task {} to ERRORED while handling "
                        "an unhandled capability exception. {}: {}",
                        self,
                        task,
                        transition_exc.__class__.__name__,
                        str(transition_exc),
                    )

            # Upon returning from the task's execution method the capability is no longer
            # running, so drop its inbox (no more results will be routed to it) and update
            # the task's completion datetime. The outbox is intentionally left in
            # self._task_outboxes so any buffered output can still be drained.
            self._task_inboxes.pop(str(task_launch_message.task_id), None)
            task.datetime_completed = datetime.now()

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
        # The inbox is tracked while the capability runs so results can be routed to it;
        # it is dropped on completion (see the handler). The outbox is tracked separately
        # so readers can drain it even after the capability exits: it is removed only when
        # it reaches end of stream, not when the capability finishes.
        self._task_inboxes[str(task.task_id)] = (
            running_agent_capability._task_messages_inbox
        )
        self._task_outboxes[str(task.task_id)] = (
            running_agent_capability._task_messages_outbox
        )
        self._new_task_started_event.set()

        agent_capability_task = asyncio.create_task(
            _agent_capability_task_handler(
                agent_capability=running_agent_capability,
                task=task,
            ),
        )
        # Hold a reference keyed by task ID to prevent garbage collection while running
        # and to allow cancelling this specific handler on deletion.
        self._task_handler_async_tasks[str(task.task_id)] = agent_capability_task
        # Once the task is finished it removes its own reference to avoid holding
        # references to finished handlers indefinitely.
        agent_capability_task.add_done_callback(
            lambda _task, task_id=str(task.task_id): self._task_handler_async_tasks.pop(
                task_id, None
            )
        )
