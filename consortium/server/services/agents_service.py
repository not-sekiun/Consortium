import uuid
from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger

from consortium.framework.agents.agent_message_models import (
    Payload,
    RegistrationMessageModel,
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.task_objects import Task
from consortium.server.services.events_service import EventsService
from consortium.server.services.task_runtime_service import TaskRuntimeService
from consortium.server.services.tasks_service import TasksService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
    run_async_background_task,
    utc_now,
)


class AgentsService:
    def __init__(
        self,
        events_service: EventsService,
        tasks_service: TasksService,
        task_runtime_service: TaskRuntimeService,
    ):
        self._events_service = events_service
        self._tasks_service = tasks_service
        self._task_runtime_service = task_runtime_service
        self._agents = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self) -> str:
        return "Agents Service"

    def __repr__(self) -> str:
        return "AgentsService()"

    @log_and_propagate_error_on_service_method
    def register_agent(
        self,
        listener_id: str | uuid.UUID,
        registration_message: RegistrationMessageModel | None = None,
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
    ) -> Agent:
        """Registers a new agent and emits an `AGENT_REGISTERED` event.

        Give the agent's reported details either as a whole `registration_message` or as
        individual fields.

        Args:
            listener_id: The ID of the listener this agent is connecting through.
            registration_message: The registration details reported by the agent. When
                given, it supplies every reported field and the individual field
                arguments below are ignored. Nothing an agent reports is verified by the
                server, so treat the contents as claims rather than as facts.
            payload_id: The ID of the payload that generated this agent. When `None`, the
                agent is not attributed to any payload.
            agent_type: The agent type name. When `None`, the agent has no associated
                type.
            name: A human-readable display name for the agent. When `None`,
                a name is derived from the agent's identity later.
            description: A short human-readable description of the agent. Defaults
                to an empty string when omitted.
            endpoint: A human-readable string identifying the agent's network endpoint.
                Defaults to an empty string when omitted.
            user: The OS username the agent process is running as. When `None`, the
                running user is unknown.
            is_admin: Whether the agent is running with administrator or root privileges.
                When `None`, the privilege level is unknown.
            os: The name of the host operating system (for example "Windows"). When
                `None`, the OS is unknown.
            version: The version string of the host operating system. When `None`, the
                version is unknown.
            arch: The CPU architecture of the host system (for example "x86_64"). When
                `None`, the architecture is unknown.
            pid: The process ID of the agent on its host. When `None`, the PID is
                unknown.
            locale: The locale string of the host system (for example "en_US"). When
                `None`, the locale is unknown.
            remote_ip: The IP address the agent is reachable at. When `None`, the remote
                address is unknown.
            local_ip: The local IP address of the agent's host as seen by the agent
                itself. When `None`, the local address is unknown.
            hostname: The hostname of the agent's host. When `None`, the hostname is
                unknown.
            agent_data: Arbitrary key-value pairs carrying agent-specific metadata not
                covered by the other fields. When `None`, no extra metadata is stored.

        Returns:
            The newly registered agent instance.

        Raises:
            AgentCreationParameterTypeError: If any of the provided parameters is not of
                the type the agent expects.
            ListenerNotFoundError: If no listener with the given `listener_id` is
                registered.
            AgentTypeResolutionError: If the agent's type cannot be resolved, either
                because neither `payload_id` nor `agent_type` was provided, because
                `payload_id` does not correspond to a known payload, or because
                `agent_type` does not name a known agent type.
        """
        # A whole message wins over the individual fields rather than merging with them:
        # the two describe the same agent, and a merge would silently mix a validated
        # report with values the caller supplied separately.
        if registration_message is not None:
            payload_id = registration_message.payload_id
            agent_type = registration_message.agent_type
            endpoint = registration_message.endpoint
            user = registration_message.user
            is_admin = registration_message.is_admin
            os = registration_message.os
            version = registration_message.version
            arch = registration_message.arch
            pid = registration_message.pid
            locale = registration_message.locale
            remote_ip = registration_message.remote_ip
            local_ip = registration_message.local_ip
            hostname = registration_message.hostname
            agent_data = registration_message.agent_data

        agent = Agent(
            tasks_service=self._tasks_service,
            task_runtime_service=self._task_runtime_service,
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
        self._agents[str(agent.agent_id)] = agent

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_REGISTERED,
                message=f"Registered agent: {agent}",
                data=agent.to_json(),
            )
        )
        self._logger.info("Registered agent: {}", agent)
        self._logger.debug("- {!r}", agent)

        return agent

    @log_and_propagate_error_on_service_method
    def deregister_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        """Removes a registered agent from the service and emits an `AGENT_DEREGISTERED` event.

        Args:
            agent_id: The ID of the agent to deregister.

        Raises:
            AgentNotFoundError: If no agent with the given ID is registered.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        self._tasks_service._error_pending_tasks_for_agent(
            agent=agent,
            error_message="The owning agent deregistered before this task completed.",
        )
        del self._agents[str(agent.agent_id)]

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_DEREGISTERED,
                message=f"Deregistered agent: {agent}",
                data=agent.to_json(),
            )
        )
        self._logger.info("Deregistered agent: {}", agent)
        self._logger.debug("- {!r}", agent)

    @log_and_propagate_error_on_service_method
    async def delete_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        """Deletes a registered agent from the service and emits an `AGENT_DELETED` event.

        Unlike `deregister_agent_by_agent_id`, which reflects an agent that has left of
        its own accord, this is an operator-initiated removal of the agent regardless of
        whether it is still active.

        Args:
            agent_id: The ID of the agent to delete.

        Raises:
            AgentNotFoundError: If no agent with the given ID is registered.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        self._tasks_service._error_pending_tasks_for_agent(
            agent=agent,
            error_message=(
                "The owning agent was deleted by an operator before this task "
                "completed."
            ),
        )
        del self._agents[str(agent.agent_id)]

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_DELETED,
                message=f"Deleted agent: {agent}",
                data=agent.to_json(),
            )
        )
        self._logger.info("Deleted agent: {}", agent)
        self._logger.debug("- {!r}", agent)

    @log_and_propagate_error_on_service_method
    def check_in_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        """Records a check-in from an agent, updating its last activity timestamp and marking it active.

        Emits an `AGENT_CHECKED_IN` event.

        Args:
            agent_id: The ID of the agent checking in.

        Raises:
            AgentNotFoundError: If no agent with the given ID is registered.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_CHECKED_IN,
                message=f"Checked in agent: {agent}",
                data=agent.to_json(),
            )
        )
        agent.datetime_last_checked_in = utc_now()
        agent.mark_as_active()
        self._logger.debug("Checked in agent {!r}", agent)

    @log_and_propagate_error_on_service_method
    async def get_next_task_message_by_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
        timeout: float | None = None,
    ) -> TaskInputMessageModel | TaskOutputMessageModel | None | object:
        """Get the next task message produced by a running capability of an agent for a
        specific task.

        Args:
            agent_id: The agent ID of the agent to read the task message from.
            task_id: The task ID of the running task whose next message to read.
            timeout: Maximum time in seconds to wait for the next message. If None, waits
                indefinitely. If 0, polls without blocking.

        Returns:
            The next task message produced by the task's capability, `None` if the timeout
            elapsed before a message was produced (poll again), or END_OF_STREAM if the
            capability has finished and its outbox is fully drained (move on).

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.
            AgentTaskNotFoundError: Raised if the task with the specified task ID is not
                found on the agent.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        return await agent.get_next_task_message_by_task_id(
            task_id=task_id, timeout=timeout
        )

    @log_and_propagate_error_on_service_method
    async def get_next_task_message_sequential(
        self,
        agent_id: str | uuid.UUID,
        timeout: float | None = None,
    ) -> TaskInputMessageModel | TaskOutputMessageModel | None:
        """Get the next task message from the earliest running capability of an agent.

        Messages are drained from the earliest started capability until it completes
        before moving on to the next one, preserving a strict per-capability ordering.

        Args:
            agent_id: The agent ID of the agent to read the task message from.
            timeout: Maximum time in seconds to wait for the next message, spanning both
                the wait for a capability to start and the wait for it to produce a
                message. If None, waits indefinitely. If 0, polls without blocking.

        Returns:
            The next task message from the earliest running capability, or None if the
            timeout elapsed before a message was produced.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        return await agent.get_next_task_message_sequential(timeout=timeout)

    @log_and_propagate_error_on_service_method
    async def get_next_task_message_any(
        self,
        agent_id: str | uuid.UUID,
        timeout: float | None = None,
    ) -> TaskLaunchMessageModel | TaskOutputMessageModel | None:
        """Get the next task message from any running capability of an agent.

        Returns the first message produced by any running capability, interleaving
        (muxing) messages across capabilities in the order they become available.

        Args:
            agent_id: The agent ID of the agent to read the task message from.
            timeout: Maximum time in seconds to wait for the next message, spanning both
                the wait for a capability to start and the wait for one to produce a
                message. If None, waits indefinitely. If 0, polls without blocking.

        Returns:
            The next task message from any running capability, or None if the timeout
            elapsed before a message was produced.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        return await agent.get_next_task_message_any(timeout=timeout)

    async def drain_task_messages_by_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Drain task messages from a specific running task of an agent until it completes.

        Yields each message produced by the task's capability in order, terminating when
        the capability finishes.

        Args:
            agent_id: The agent ID of the agent to drain task messages from.
            task_id: The task ID of the running task whose messages to drain.

        Yields:
            Each task message produced by the task's capability, in the order produced.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.
            AgentTaskNotFoundError: Raised if the task with the specified task ID is not
                found on the agent.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        async for task_message in agent.drain_task_messages_by_task_id(task_id=task_id):
            yield task_message

    async def drain_task_messages_sequential(
        self,
        agent_id: str | uuid.UUID,
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Drain task messages from an agent one capability at a time.

        Yields messages from the earliest started capability until it completes before
        moving on to the next one, preserving a strict per-capability ordering. Loops
        indefinitely, waiting for new capabilities to start as needed.

        Args:
            agent_id: The agent ID of the agent to drain task messages from.

        Yields:
            Each task message, drained from the earliest running capability first.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        async for task_message in agent.drain_task_messages_sequential():
            yield task_message

    async def drain_task_messages_any(
        self,
        agent_id: str | uuid.UUID,
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Drain task messages from any running capability of an agent.

        Yields messages from any running capability, interleaving (muxing) them in the
        order they become available. Loops indefinitely, waiting for new capabilities to
        start as needed.

        Args:
            agent_id: The agent ID of the agent to drain task messages from.

        Yields:
            Each task message, in the order it becomes available across all running
            capabilities.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        async for task_message in agent.drain_task_messages_any():
            yield task_message

    @log_and_propagate_error_on_service_method
    async def dispatch_task_output_message(
        self,
        agent_id: str | uuid.UUID,
        task_output_message: TaskOutputMessageModel | None = None,
        task_id: str | uuid.UUID | None = None,
        success: bool | None = None,
        message: str = "",
        data: dict[str, Any] | None = None,
        payload: Payload | bytes | bytearray | None = None,
    ) -> None:
        """Dispatch a task output message for a running task on an agent.

        Give the agent's reported result either as a whole `task_output_message` or as
        individual fields.

        Args:
            agent_id: The agent ID of the agent to submit the result
                for.
            task_output_message: The task output message reported by the agent,
                identifying the task it belongs to and carrying any result data and
                binary payload. When given, the individual field arguments below are
                ignored.
            task_id: The task ID of the task to submit the result for. Required when
                `task_output_message` is not given.
            success: Whether the task was successful. Required when
                `task_output_message` is not given.
            message: A message describing the result.
            data: The result data.
            payload: Optional binary payload associated with the result.

        Raises:
            ValueError: Raised if neither `task_output_message` nor both of `task_id`
                and `success` were given, so there is no result to dispatch.
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.
            ValidationError: Raised if the arguments provided fail validation of the
                task output message they are assembled into, for example a `task_id`
                that is not a valid UUID or `data` that is not JSON serializable. Left
                unwrapped as it describes the arguments the caller supplied rather than
                a failure of the agent or its task.

        Note:
            A task output message whose task ID does not correspond to a running task
            (the task completed, timed out or was deleted) is a benign lifecycle race,
            it is logged and dropped rather than raised.
        """
        # A whole message wins over the individual fields rather than merging with them:
        # the two describe the same result, and a merge would silently mix a validated
        # report with values the caller supplied separately.
        if task_output_message is None:
            if task_id is None or success is None:
                raise ValueError(
                    "dispatch_task_output_message requires either a "
                    "'task_output_message', or both a 'task_id' and a 'success'."
                )
            task_output_message = TaskOutputMessageModel(
                task_id=task_id,
                success=success,
                message=message,
                data=data if data is not None else {},
                payload=payload,
            )

        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        await agent.dispatch_task_output_message(
            task_output_message=task_output_message,
        )
        self._logger.debug(
            "Submitted result for task ID {} to agent {!r}",
            task_output_message.task_id,
            agent,
        )

    @log_and_propagate_error_on_service_method
    def get_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> Agent:
        """Returns a registered agent by its ID.

        Args:
            agent_id: The ID of the agent to retrieve.

        Returns:
            The agent with the specified ID.

        Raises:
            AgentNotFoundError: If no agent with the given ID is registered.
        """
        agent_id = normalize_uuid(value=agent_id)

        try:
            agent = self._agents[agent_id]
        except KeyError:
            raise AgentNotFoundError(agent_id=agent_id) from None

        self._logger.debug("Retrieved agent: {!r}", agent)
        return agent

    @log_and_propagate_error_on_service_method
    def get_all_agents(self) -> list[Agent]:
        """Returns all registered agents.

        Returns:
            A list of all registered agents. Empty if none are registered.
        """
        all_agents = list(self._agents.values())
        self._logger.debug(
            "Retrieved all agents ({} retrieved)",
            len(all_agents),
        )
        return all_agents

    @log_and_propagate_error_on_service_method
    async def task_agent_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        command: str,
        arguments: dict[str, Any],
    ) -> Task:
        """Queues a command for execution on the specified agent and emits an `AGENT_TASKED` event.

        The tasking is validated before any task is created. When validation rejects it
        no task is registered and no `AGENT_TASKED` event is emitted, the relevant
        exception below is raised instead.

        Args:
            agent_id: The ID of the agent to task.
            command: The name of the command to execute on the agent.
            arguments: The arguments to pass along with the command. Omitted optional
                options are filled in from their declared defaults.

        Returns:
            The newly created task object representing the queued command.

        Raises:
            AgentNotFoundError: If no agent with the given ID is registered.
            AgentCapabilityNotFoundError: If command does not name a capability of the
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
        agent = self.get_agent_by_agent_id(agent_id=agent_id)

        task = await agent.submit_task(command=command, arguments=arguments)

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.AGENT_TASKED,
                message=f"Tasked agent: {agent}",
                data={
                    "agent_id": str(agent.agent_id),
                    "task": task.to_json(),
                },
            )
        )
        self._logger.info("Tasked agent {} with task {}", agent, task)
        self._logger.debug("Tasked agent {!r} with task {!r}", agent, task)
        return task

    @log_and_propagate_error_on_service_method
    def update_agent_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Agent:
        """Updates the name and/or description of a registered agent.

        Emits an `AGENT_UPDATED` event when at least one field changes. Passing `None`
        for a field leaves it unchanged.

        Args:
            agent_id: The ID of the agent to update.
            name: The new display name for the agent. When `None`, the
                name is not changed.
            description: The new description for the agent. When `None`,
                the description is not changed.

        Returns:
            The updated agent instance.

        Raises:
            AgentNotFoundError: If no agent with the given ID is registered.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)

        updated = {}

        if name is not None:
            old_name = agent.name
            agent.name = name
            self._logger.info(
                "Updated agent {} name from '{}' to '{}'",
                agent,
                old_name,
                agent.name,
            )
            self._logger.debug("- {!r}", agent)
            updated["name"] = {
                "old": old_name,
                "new": agent.name,
            }

        if description is not None:
            old_description = agent.description
            agent.description = description
            self._logger.debug(
                "Updated agent {} description from '{}' to '{}'",
                agent,
                old_description,
                agent.description,
            )
            self._logger.debug("- {!r}", agent)
            updated["description"] = {
                "old": old_description,
                "new": agent.description,
            }

        if updated:
            run_async_background_task(
                coroutine=self._events_service.trigger_event(
                    event_type=EventType.AGENT_UPDATED,
                    message=f"Updated agent: {agent}",
                    data=agent.to_json(),
                )
            )
        else:
            self._logger.debug(
                "No updates applied to agent {} as no changes were detected even "
                "though the update method was called",
                agent,
            )

        return agent
