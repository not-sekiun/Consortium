import asyncio
import uuid
from collections.abc import AsyncGenerator
from enum import StrEnum
from typing import TYPE_CHECKING, Any, get_type_hints

from loguru import logger
from pydantic import UUID4, BaseModel, JsonValue, ValidationError

from consortium.framework._core.components import State
from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCapabilityExecutionError,
    AgentCapabilityLaunchError,
)
from consortium.framework._core.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError as OptionValueValidationFrameworkError,
)
from consortium.framework.agents import BaseAgentCapability, TaskInputMessageModel
from consortium.framework.agents._task_messages_queue import END_OF_STREAM
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.event_hooks import EventType
from consortium.framework.listeners import BaseListener
from consortium.framework.signal_exceptions.agent_capabilties_signal_exception import (
    AgentCapabilityExecutionError as AgentCapabilityExecutionSignalError,
    AgentCapabilityLaunchError as AgentCapabilityLaunchSignalError,
)
from consortium.framework.signal_exceptions.options_signal_exceptions import (
    OptionValueValidationError as OptionValueValidationSignalError,
)
from consortium.server import server_singletons as server_singletons
from consortium.server.exceptions.object_exceptions.agent_object_exceptions import (
    AgentCapabilityNotFoundError,
    AgentCapabilityOptionNotFoundError,
    AgentCapabilityOptionValueValidationError,
    AgentCapabilityValidatingFunctionError,
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
from consortium.server.exceptions.service_exceptions.tasks_service_exceptions import (
    TaskNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.task_objects import Task, TaskState
from consortium.server.objects.task_runtime import TaskRuntime
from consortium.server.utils import (
    generate_random_human_readable_name,
    normalize_uuid,
    utc_now,
)

if TYPE_CHECKING:
    from consortium.server.services.task_runtime_service import TaskRuntimeService
    from consortium.server.services.tasks_service import TasksService


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
        tasks_service: TasksService,
        task_runtime_service: TaskRuntimeService,
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

        self.logger = logger.bind(
            logger_name=f"Agent {self}",
            logger_type=LoggerType.AGENT_LOGGER,
        )
        self.datetime_first_checked_in = utc_now()
        self.datetime_last_checked_in = utc_now()

        self._tasks_service = tasks_service
        self._task_runtime_service = task_runtime_service
        # By default, agents are considered ACTIVE when created. `self._status` is used
        # to track the reported status of the agent while the framework may
        # automatically infer other statuses such as ORPHANED or UNREACHABLE based on
        # the state of the attached listener. Even if an agent was marked as ACTIVE or
        # INACTIVE by the listener, the moment it is not running or deleted, the agent
        # state will be ORPHANED or UNREACHABLE respectively.
        self._status = AgentStatus.ACTIVE
        # Fired when a new task is started (specifically after its runtime is attached
        # to the registry). This is used specifically and only to wake up
        # self.get_next_task_message_sequential() when it is called with a timeout of
        # `None` while there are no readable outboxes since it will block indefinitely
        # until the first valid task message can be pulled out
        self._new_task_started_event = asyncio.Event()
        # Shared across all of this agent's capability outboxes: every successful put on
        # an outbox notifies this condition. get_next_task_message_any waits on it to be
        # woken the moment any running capability produces a message, then scans the
        # outboxes in insertion order for the first one with a pending message.
        self._outbox_activity = asyncio.Condition()

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

    async def submit_task(self, command: str, arguments: dict[str, JsonValue]) -> Task:
        """Validate a tasking, start its capability and register the resulting task.

        Args:
            command: The name of the capability to run, matched against the capabilities
                of this agent's type.
            arguments: The arguments to run the capability with, keyed by option name.
                Omitted optional options are filled in from their declared defaults. The
                provided dictionary is not mutated.

        Returns:
            The registered task, QUEUED with its capability started.

        Raises:
            AgentCapabilityNotFoundError: If command does not name a capability of this
                agent's type.
            MissingRequiredAgentCapabilityOptionError: If a required option is absent
                from arguments.
            AgentCapabilityOptionNotFoundError: If arguments contains an unknown option
                name.
            AgentCapabilityOptionValueValidationError: If an argument value fails type or
                constraint validation.
            AgentCapabilityValidatingFunctionError: If the capability's validating
                function rejects the resolved argument set.
        """
        # Validation runs before the task is constructed, so a rejected tasking was
        # never queued and leaves nothing behind: no task ID is minted, no record is
        # registered and no event is emitted. Every exception documented above escapes
        # from here, which is what lets the API answer a bad tasking with a 422 rather
        # than a task the operator then has to inspect to discover it never ran.
        if command not in self.agent_type.agent_capabilities:
            raise AgentCapabilityNotFoundError(
                command=command,
                agent_str=str(self),
                agent_type_str=str(self.agent_type),
            )

        agent_capability = self.agent_type.agent_capabilities[command]

        # Check for missing required options before filling in defaults, so that a
        # required option with default_value=None is caught rather than silently
        # accepted. This mirrors the ordering the listener and agent template option
        # resolution uses.
        for option_name, option in agent_capability.options.items():
            if option.required and option_name not in arguments:
                raise MissingRequiredAgentCapabilityOptionError(
                    agent_str=str(self),
                    agent_capability_name=agent_capability.name,
                    option_name=option_name,
                )

        # Fill in default option values for options that were not provided in the
        # arguments dictionary. For options that do not have a default value
        # they fill in as `None`
        resolved_arguments: dict[str, JsonValue] = dict(arguments)
        for option_name, option in agent_capability.options.items():
            if option_name not in resolved_arguments:
                resolved_arguments[option_name] = option.default_value

        # Validate entire constructed argument set.
        for option_name, value in resolved_arguments.items():
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
            except OptionValueValidationFrameworkError as exc:
                raise AgentCapabilityOptionValueValidationError(
                    option_name=option_name,
                    option_value=value,
                    agent_str=str(self),
                    error_message=str(exc),
                ) from None

        # Run validation function on the entire set of arguments if one was provided.
        if agent_capability.validating_function:
            try:
                agent_capability.validating_function(resolved_arguments)
            except OptionValueValidationSignalError as exc:
                raise AgentCapabilityValidatingFunctionError(
                    agent_str=str(self),
                    command=agent_capability.name,
                    error_message=exc.message,
                    detail=exc.detail,
                ) from None

        task = Task(
            agent_id=self.agent_id,
            command=command,
            arguments=resolved_arguments,
        )

        # Starting the capability and registering its record is one synchronous
        # sequence: _start_agent_capability has no suspension point, so the event loop
        # cannot interleave and no reader can observe the intermediate state. That is
        # what allows the record to be registered last, which is what makes this
        # transactional without a rollback path. A capability that fails to construct
        # raises before anything is stored, leaving nothing behind to undo. Nothing
        # that can raise may be introduced after the handler is created, and no await
        # may be introduced anywhere in this sequence.
        await self._start_agent_capability(
            agent_capability=agent_capability,
            task=task,
        )
        self._tasks_service._register_task(task=task, agent=self)

        # Signalled only once the record exists so a woken muxer always resolves it.
        self._new_task_started_event.set()

        return task

    async def get_next_task_message_by_task_id(
        self,
        task_id: str | uuid.UUID,
        timeout: float | None = None,
    ) -> TaskLaunchMessageModel | TaskInputMessageModel | None | object:
        """Get the next task message produced by the capability for the specified task.

        Reads follow the registered runtime's outbox lifecycle, not the capability's: a
        capability may stream messages and then exit, and those buffered messages must
        remain readable until drained.

        Returns the next task message, or `None` when `timeout` elapses with nothing
        available (a transient "nothing yet, poll again" signal). Returns END_OF_STREAM
        once the outbox is exhausted (shut down and fully drained, or never produced), at
        which point the outbox is dropped and every subsequent read returns
        END_OF_STREAM."""
        task = self.get_task_by_task_id(task_id=task_id)

        # A missing runtime or outbox means it was never produced, was torn down, or has
        # already been fully drained, so the stream is over.
        runtime = self._task_runtime_service.get_task_runtime(task_id=task.task_id)
        if runtime is None or runtime.outbox is None:
            return END_OF_STREAM
        outbox = runtime.outbox

        try:
            task_message = await outbox.get(timeout=timeout)
        except TimeoutError:
            # A timeout means "nothing available yet". We surface it as `None` (distinct
            # from END_OF_STREAM) so callers can tell a transient miss they should poll
            # again from an exhausted stream they should move on from.
            return None

        if task_message is END_OF_STREAM:
            # End of stream: the capability finished and the outbox is fully drained, so
            # drop it. Subsequent reads for this task return END_OF_STREAM.
            self._task_runtime_service.release_outbox(task_id=task.task_id)
            return END_OF_STREAM

        # The task may have been deleted after outbox.get dequeued a message but before
        # this coroutine resumed. Deleted records must never deliver a message.
        if (
            self._tasks_service.find_task(
                task_id=task.task_id,
                agent_id=self.agent_id,
            )
            is None
        ):
            return END_OF_STREAM

        # The launch message is the first thing a capability puts on its outbox. Popping
        # it is the point at which the agent has acknowledged and picked up the task, so
        # transition it from QUEUED to RUNNING. This gate is required because
        # dispatch_task_output_message drops any result for a task that is not RUNNING.
        # The compare and swap only succeeds from QUEUED, so a task whose capability
        # already completed (streamed then exited) and is only now being drained stays
        # terminal, and a task that reached a terminal state while this coroutine was
        # suspended in outbox.get above is not dragged back to RUNNING.
        if (
            isinstance(task_message, TaskLaunchMessageModel)
            and task.status._try_transition_to_running()
        ):
            task.datetime_started = utc_now()

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
        if self._task_runtime_service.has_readable_outbox_for_agent(
            agent_id=self.agent_id
        ):
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
    ) -> TaskInputMessageModel | TaskLaunchMessageModel | None:
        """Get the next task message from the earliest tasked outbox, draining it
        completely (including any messages a streamed-and-exited capability left behind)
        before moving on to the next one.

        End of stream is a per-outbox concept, but the set of outboxes this muxes over
        has no collective end (a new task can always start), so this never surfaces
        END_OF_STREAM: when the earliest outbox is exhausted it is dropped and this
        transparently advances to the next one. Returns the next message, or `None` when
        `timeout` elapses with nothing produced."""
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        while True:
            # Clamp to 0.0 rather than early-returning on an exhausted budget: a
            # timeout of 0 must still get one non-blocking poll of the earliest outbox
            # below, and the budget is ultimately enforced by the waits it feeds.
            remaining = None if deadline is None else max(deadline - loop.time(), 0.0)

            ready, remaining = await self._wait_for_a_readable_outbox(timeout=remaining)
            if not ready:
                return None

            # The registry maintains insertion order per agent, so this is the earliest
            # tasked live runtime with a readable outbox.
            task_id = self._task_runtime_service.first_readable_task_id_for_agent(
                agent_id=self.agent_id
            )
            if task_id is None:
                continue
            try:
                task_message = await self.get_next_task_message_by_task_id(
                    task_id=task_id, timeout=remaining
                )
            except AgentTaskNotFoundError:
                # The muxer selected this task itself. Deletion between selection and
                # read is a benign lifecycle race, so advance to the next record.
                continue
            if task_message is END_OF_STREAM:
                # Earliest outbox exhausted and released; advance to the next one. A
                # shut down, drained outbox returns END_OF_STREAM immediately, so this is
                # instantaneous and the loop stays bounded by the number of outboxes;
                # the budget is enforced by the reads above.
                continue
            # A message, or `None` if the budget elapsed with nothing produced.
            return task_message

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
        for task_id, outbox in self._task_runtime_service.readable_outboxes_for_agent(
            agent_id=self.agent_id
        ):
            if not outbox.empty():
                found_task_id = task_id
                break
            if outbox.is_at_end_of_stream():
                ended_task_ids.append(task_id)
        for task_id in ended_task_ids:
            self._task_runtime_service.release_outbox(task_id=task_id)
        return found_task_id

    async def get_next_task_message_any(
        self, timeout: float | None = None
    ) -> TaskLaunchMessageModel | TaskInputMessageModel | None:
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
            try:
                task_message = await self.get_next_task_message_by_task_id(
                    task_id=task_id, timeout=0
                )
            except AgentTaskNotFoundError:
                # The muxer selected this task itself, so disappearance here is a
                # lifecycle race rather than invalid caller input.
                continue
            if task_message is not None and task_message is not END_OF_STREAM:
                return task_message
            # `None` (the message was taken by another reader) or END_OF_STREAM (the
            # outbox drained to end of stream) between the scan and the read. Loop and
            # wait for the next one.

    async def drain_task_messages_by_task_id(
        self, task_id: str | uuid.UUID
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Infinitely loop and drain task messages from a task until it completes"""
        while True:
            task_message = await self.get_next_task_message_by_task_id(
                task_id=task_id, timeout=None
            )
            # With timeout=None the read only ever returns a message or END_OF_STREAM
            # (never a `None` timeout), so end of stream is the sole terminating signal.
            if task_message is END_OF_STREAM:
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

        if task.status.state != TaskState.RUNNING:
            self.logger.warning(
                "Agent {} received a task output message for task {} with status {} "
                "that is not running. The message was dropped.",
                self,
                task,
                task.status,
            )
            return False

        # A running task should always have a live runtime with an attached inbox. If it
        # does not, the capability finished or was torn down concurrently, so drop and
        # log rather than dereferencing a missing entry out of the dispatch path.
        runtime = self._task_runtime_service.get_task_runtime(task_id=task.task_id)
        if runtime is None or runtime.inbox is None:
            self.logger.warning(
                "Agent {} received a task output message for a running task {} but no "
                "inbox is tracked for it. The message was dropped.",
                self,
                task,
            )
            return False

        try:
            await runtime.inbox.put(task_message=task_output_message)
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
        state: TaskState | None = None,
    ) -> list[Task]:
        return self._tasks_service.get_all_tasks(
            agent_id=self.agent_id,
            status=state,
        )

    def get_all_queued_tasks(self) -> list[Task]:
        return self.get_all_tasks(state=TaskState.QUEUED)

    def get_all_running_tasks(self) -> list[Task]:
        return self.get_all_tasks(state=TaskState.RUNNING)

    def get_all_succeeded_tasks(self) -> list[Task]:
        return self.get_all_tasks(state=TaskState.SUCCEEDED)

    def get_all_failed_tasks(self) -> list[Task]:
        return self.get_all_tasks(state=TaskState.FAILED)

    def get_all_errored_tasks(self) -> list[Task]:
        return self.get_all_tasks(state=TaskState.ERRORED)

    def get_task_by_task_id(
        self,
        task_id: str | uuid.UUID,
        state: TaskState | None = None,
    ) -> Task:
        task = self._tasks_service.find_task(
            task_id=task_id,
            agent_id=self.agent_id,
            status=state,
        )
        if task is None:
            raise AgentTaskNotFoundError(task_id=normalize_uuid(value=task_id))
        return task

    def get_queued_task_by_task_id(self, task_id: str | uuid.UUID) -> Task:
        return self.get_task_by_task_id(task_id=task_id, state=TaskState.QUEUED)

    def get_running_task_by_task_id(self, task_id: str | uuid.UUID) -> Task:
        return self.get_task_by_task_id(task_id=task_id, state=TaskState.RUNNING)

    def get_succeeded_task_by_task_id(self, task_id: str | uuid.UUID) -> Task:
        return self.get_task_by_task_id(task_id=task_id, state=TaskState.SUCCEEDED)

    def get_failed_task_by_task_id(self, task_id: str | uuid.UUID) -> Task:
        return self.get_task_by_task_id(task_id=task_id, state=TaskState.FAILED)

    def get_errored_task_by_task_id(self, task_id: str | uuid.UUID) -> Task:
        return self.get_task_by_task_id(task_id=task_id, state=TaskState.ERRORED)

    async def delete_task_by_task_id(self, task_id: str | uuid.UUID) -> None:
        if (
            self._tasks_service.find_task(
                task_id=task_id,
                agent_id=self.agent_id,
            )
            is None
        ):
            raise AgentTaskNotFoundError(task_id=str(task_id))
        try:
            # Only a vanished record is translated. TaskNotDeletableError propagates as
            # itself: the task provably belongs to this agent, having just resolved
            # through the agent scoped lookup above, so reporting it as not found would
            # describe a running task as a missing one.
            await self._tasks_service.delete_task_by_task_id(task_id=task_id)
        except TaskNotFoundError:
            raise AgentTaskNotFoundError(task_id=str(task_id)) from None

    def error_pending_tasks(self, error_message: str) -> list[Task]:
        return self._tasks_service._error_pending_tasks_for_agent(
            agent=self,
            error_message=error_message,
        )

    def mark_as_active(self) -> None:
        self._status = AgentStatus.ACTIVE

    def mark_as_inactive(self) -> None:
        self._status = AgentStatus.INACTIVE

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "agent_id": str(self.agent_id),
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            # An agent cannot be constructed without a resolvable agent type (see
            # `AgentTypeResolutionError` in `__init__`), so this is never `None`.
            "agent_type": self.agent_type.to_json(),
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
            "connected_listener": self.connected_listener.to_json_reference()
            if self.connected_listener is not None
            else None,
            "agent_data": self.agent_data,
        }

    def to_json_reference(self) -> dict[str, JsonValue]:
        # A live reference: the agent is in memory here, so the full agent type
        # descriptor is embedded. Persistent references (recorded against artifacts)
        # instead store the agent type by name, see `PersistentAgentReferenceModel`.
        return {
            "agent_id": str(self.agent_id),
            "name": self.name,
            "agent_type": self.agent_type.to_json(),
        }

    async def _start_agent_capability(
        self,
        agent_capability: type[BaseAgentCapability],
        task: Task,
    ) -> None:
        async def _agent_capability_task_handler(
            agent_capability: BaseAgentCapability,
            task: Task,
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

                # execute() returning after a cancellation was requested means the
                # capability caught its own CancelledError instead of letting it
                # propagate. Teardown cancels the handler before it errors the task
                # or destroys the record, so resuming here would drive a terminal
                # transition, and fire AGENT_TASK_COMPLETED, for a task that is
                # already terminal or already deleted. Re-assert the cancellation
                # the capability suppressed: cancelling() is non-zero from the
                # moment cancel() is called, whether or not the exception survived
                # the capability body.
                handler_async_task = asyncio.current_task()
                if handler_async_task is not None and handler_async_task.cancelling():
                    # Named rather than silently re-raised: the framework recovers, but
                    # a capability that suppresses cancellation is a component bug and
                    # recovering quietly would leave it undiagnosable.
                    self.logger.warning(
                        "Agent {} had capability '{}' suppress the cancellation of "
                        "task {} and return normally. The framework re-asserted the "
                        "cancellation, but capabilities must let CancelledError "
                        "propagate rather than catching it and returning.",
                        self,
                        agent_capability.name,
                        task.task_id,
                    )
                    raise asyncio.CancelledError

                # Upon returning without raising an error check the `task_outcome` to
                # see if it is present or not and emit the final event based on that
                if isinstance(task_outcome, Success):
                    # A task reporting Success while still QUEUED means it completed
                    # without the agent ever popping its launch message (never
                    # transitioned through RUNNING). This is allowed for now but is
                    # likely a capability bug, warn so it can be investigated.
                    if task.status.state == TaskState.QUEUED:
                        self.logger.warning(
                            "Agent {} completed task {} to SUCCESS but the task never "
                            "left QUEUED, its launch message was never popped so it was "
                            "never acknowledged by the agent nor transitioned through "
                            "RUNNING.",
                            self,
                            task,
                        )
                    task.status._transition_to_succeeded()
                    task.event_logger.success(
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
                    task.event_logger.failure(
                        message=task_outcome.message,
                        data=task_outcome.data,
                    )
                elif task_outcome is None:
                    # None = the capability used the log-only events pattern and
                    # completed normally without opting in to an explicit outcome. Treat
                    # it as a normal completion: transition to SUCCEEDED without
                    # appending a duplicate terminal event (the capability already
                    # logged whatever events it wanted via log_*).
                    if task.status.state == TaskState.QUEUED:
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
            except AgentCapabilityLaunchSignalError as exc:
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
                task.event_logger.failure(
                    message=exc.message,
                    data={"detail": exc.detail},
                )
            except AgentCapabilityExecutionSignalError as exc:
                # Deliberately raised from on_execute to stop a running capability with a
                # runtime error. Reported as ERRORED with the execution base message.
                task.status._transition_to_errored(
                    error=AgentCapabilityExecutionError(
                        agent_capability_name=agent_capability.name,
                        error_message=exc.message,
                        detail=exc.detail,
                    )
                )
                task.event_logger.failure(
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
                # This is the last-resort error handler running inside a fire and
                # forget asyncio task, so it must not raise. A compare and swap covers
                # the one way the transition can legitimately fail: the capability
                # suppressed its own cancellation and then raised something else while
                # cleaning up, so agent teardown already drove this task terminal. That
                # is a lost race rather than an error, so log it and leave the terminal
                # state teardown already recorded in place.
                if task.status._try_transition_to_errored(
                    error=AgentCapabilityExecutionError(
                        agent_capability_name=agent_capability.name,
                        error_message=(
                            "An unhandled exception was raised during execution. "
                            f"{formatted_exception}"
                        ),
                    )
                ):
                    task.event_logger.error(
                        message=formatted_exception,
                        data={"type": exc.__class__.__name__, "message": str(exc)},
                    )
                else:
                    self.logger.error(
                        "Agent {} could not transition task {} to ERRORED while "
                        "handling an unhandled capability exception, it had already "
                        "reached {}.",
                        self,
                        task,
                        task.status.state,
                    )

            # Upon returning from the task's execution method the capability is no
            # longer running, so release its inbox (no more results will be routed to
            # it) and update the task's completion datetime. The outbox remains in the
            # registry so any buffered output can still be drained.
            self._task_runtime_service.release_inbox(task_id=task.task_id)
            task.datetime_completed = utc_now()

            # Finally we fire the event to notify all event handlers that a task has
            # completed
            await server_singletons.events_service.trigger_event(
                event_type=EventType.AGENT_TASK_COMPLETED,
                message=f"Agent {self} completed task {task} with status {task.status}",
                data={
                    "agent_id": str(self.agent_id),
                    "task": task.to_json(),
                },
            )

        running_agent_capability = agent_capability(agent=self, task=task)
        agent_capability_task = asyncio.create_task(
            _agent_capability_task_handler(
                agent_capability=running_agent_capability,
                task=task,
            ),
        )
        runtime = TaskRuntime()
        runtime.attach(
            handler=agent_capability_task,
            inbox=running_agent_capability._task_messages_inbox,
            outbox=running_agent_capability._task_messages_outbox,
        )
        self._task_runtime_service.attach_task_runtime(
            task_id=task.task_id,
            agent_id=self.agent_id,
            task_runtime=runtime,
        )

        # Once the handler is finished, release the registry's reference to it. The
        # callback also runs on cancellation after agent or record teardown, so a
        # missing registry entry is a normal outcome.
        agent_capability_task.add_done_callback(
            lambda _task, task_id=str(task.task_id): (
                self._task_runtime_service.release_handler(task_id=task_id)
            )
        )
