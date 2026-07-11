import asyncio
import uuid
from collections.abc import AsyncIterable
from datetime import datetime
from typing import Any

from loguru import logger

from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.objects_exceptions.agent_objects_exceptions import (
    AgentTaskNotFoundError,
)
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
)
from consortium.server.models.agent_task_models import (
    AgentTaskState,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.agent_task_objects import AgentTask
from consortium.server.services.events_service import EventsService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class AgentsService:
    def __init__(self, events_service: EventsService):
        self._events_service = events_service
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
        payload_id: str | uuid.UUID | None = None,
        agent_type: BaseAgentType | None = None,
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
    ) -> Agent:
        """Registers a new agent and emits an `AGENT_REGISTERED` event.

        Args:
            listener_id: The ID of the listener this agent is
                connecting through.
            payload_id: The ID of the payload that generated
                this agent. When `None`, the agent is not attributed to any payload.
            agent_type: The agent type classification object
                describing this agent's capabilities and command set. When `None`, the
                agent has no associated type.
            name: A human-readable display name for the agent. When `None`,
                a name is derived from the agent's identity later.
            description: A short human-readable description of the agent. Defaults
                to an empty string when omitted.
            endpoint: A human-readable string identifying the agent's network
                endpoint. Defaults to an empty string when omitted.
            user: The OS username the agent process is running as. When
                `None`, the running user is unknown.
            is_admin: Whether the agent is running with administrator or
                root privileges. When `None`, the privilege level is unknown.
            os: The name of the host operating system (for example
                "Windows"). When `None`, the OS is unknown.
            version: The version string of the host operating system. When
                `None`, the version is unknown.
            arch: The CPU architecture of the host system (for example
                "x86_64"). When `None`, the architecture is unknown.
            pid: The process ID of the agent on its host. When `None`, the
                PID is unknown.
            locale: The locale string of the host system (for example
                "en_US"). When `None`, the locale is unknown.
            remote_host_address: The IP address the agent connected from,
                as seen by the server. When `None`, the remote address is unknown.
            local_host_address: The local IP address of the agent's host as
                seen by the agent itself. When `None`, the local address is unknown.
            hostname: The hostname of the agent's host. When `None`, the
                hostname is unknown.
            agent_data: Arbitrary key-value pairs carrying
                agent-specific metadata not covered by the other fields. When `None`, no
                extra metadata is stored.

        Returns:
            The newly registered agent instance.
        """
        agent = Agent(
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
        self._agents[str(agent.agent_id)] = agent

        asyncio.create_task(
            self._events_service.trigger_event(
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
        del self._agents[str(agent.agent_id)]

        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.AGENT_DEREGISTERED,
                message=f"Deregistered agent: {agent}",
                data=agent.to_json(),
            )
        )
        self._logger.info("Deregistered agent: {}", agent)
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
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.AGENT_CHECKED_IN,
                message=f"Checked in agent: {agent}",
                data=agent.to_json(),
            )
        )
        agent.datetime_last_checked_in = datetime.now()
        agent.mark_as_active()
        self._logger.debug("Checked in agent {!r}", agent)

    @log_and_propagate_error_on_service_method
    async def get_next_agent_task_messages_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        count: int | None = None,
        block: bool = False,
        timeout: float | None = None,
    ) -> list[TaskLaunchMessageModel]:
        """Get pending task messages for an agent. This method retrieves task messages
        that are queued for the agent and returns them as a list of
        `AgentTaskMessageModel` objects.

        Args:
            agent_id: The agent ID of the agent to get tasks for.
            count: The number of tasks to retrieve. If None, retrieves
                all available tasks. If 1, retrieves a single task. If > 1, retrieves
                up to that many tasks.
            block: If True, blocks until at least one task is available.
                If False, returns immediately with whatever tasks are available
                (may be empty). Defaults to False.
            timeout: Maximum time in seconds to block waiting for tasks.
                Only applies when block=True. If None, blocks indefinitely.
                If 0, equivalent to block=False.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.

        Returns:
            A list of task messages. Returns an empty list
                if no tasks are available and block=False.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)

        # Normalize timeout=0 to non-blocking
        if timeout == 0:
            block = False

        task_messages: list[TaskLaunchMessageModel] = []

        # Determine max tasks to collect
        max_tasks = count if count is not None else float("inf")

        if block and len(task_messages) == 0:
            # Block for at least one task
            first_task = await agent.get_next_task_message(timeout=timeout)
            if first_task is not None:
                task_messages.append(first_task)

        # Collect remaining tasks (non-blocking)
        while len(task_messages) < max_tasks:
            task_message = await agent.get_next_task_message(timeout=0)
            if task_message is None:
                break
            task_messages.append(task_message)

        self._logger.debug(
            "Retrieved {} pending task(s) for agent {!r}",
            len(task_messages),
            agent,
        )

        return task_messages

    @log_and_propagate_error_on_service_method
    async def submit_result_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
        success: bool,
        message: str = "",
        data: dict[str, Any] | None = None,
        payload: AsyncIterable[bytes] | bytes | None = None,
    ) -> None:
        """Submit a result for a running task on an agent.

        Args:
            agent_id: The agent ID of the agent to submit the result
                for.
            task_id: The task ID of the task to submit the result for.
            success: Whether the task was successful.
            message: A message describing the result.
            data: The result data.
            payload: Optional binary payload
                associated with the result.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.

        Note:
            A result whose task ID does not correspond to a running task (the task
            completed, timed out or was deleted) is a benign lifecycle race, it is
            logged and dropped rather than raised.
        """
        if data is None:
            data = {}

        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        result_message = TaskOutputMessageModel(
            task_id=task_id,
            success=success,
            message=message,
            data=data,
            payload=payload,
        )
        await agent.dispatch_task_output_message(task_output_message=result_message)
        self._logger.debug(
            "Submitted result for task ID {} to agent {!r}",
            task_id,
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
    def get_all_agent_tasks(
        self, status: AgentTaskState | None = None
    ) -> list[AgentTask]:
        """Returns all tasks across every registered agent, optionally filtered by state.

        Args:
            status: When provided, only tasks in this state are
                returned. When `None`, all tasks regardless of state are returned.

        Returns:
            A list of matching tasks. Empty if no tasks match.
        """
        all_tasks = []
        for agent in self._agents.values():
            all_tasks.extend(agent.get_all_tasks(state=status))
        if status is None:
            self._logger.debug(
                "Retrieved all tasks from all agents ({} retrieved)",
                len(all_tasks),
            )
        else:
            self._logger.debug(
                "Retrieved all tasks from all agents with status {} ({} retrieved)",
                status,
                len(all_tasks),
            )
        return all_tasks

    @log_and_propagate_error_on_service_method
    def get_agent_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTask:
        """Returns a task by its ID, searching across all registered agents.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            The task with the specified ID.

        Raises:
            AgentTaskNotFoundError: If no task with the given ID exists on any agent.
        """
        for agent in self._agents.values():
            try:
                task = agent.get_task_by_task_id(task_id=task_id)
                self._logger.debug(
                    "Retrieved task {} from agent {}",
                    task_id,
                    agent,
                )
                return task
            except AgentTaskNotFoundError:
                continue

        raise AgentTaskNotFoundError(task_id=task_id) from None

    @log_and_propagate_error_on_service_method
    def get_all_agent_tasks_by_agent_id(
        self, agent_id: str | uuid.UUID, status: AgentTaskState | None = None
    ) -> list[AgentTask]:
        """Returns all tasks for a specific agent, optionally filtered by state.

        Args:
            agent_id: The ID of the agent whose tasks to retrieve.
            status: When provided, only tasks in this state are
                returned. When `None`, all tasks regardless of state are returned.

        Returns:
            A list of matching tasks. Empty if no tasks match.

        Raises:
            AgentNotFoundError: If no agent with the given ID is registered.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        all_tasks = agent.get_all_tasks(state=status)
        if status is None:
            self._logger.debug(
                "Retrieved agent tasks from agent {} ({} retrieved)",
                agent,
                len(all_tasks),
            )
        else:
            self._logger.debug(
                "Retrieved agent tasks from agent {} with status {} ({} retrieved)",
                agent,
                status,
                len(all_tasks),
            )
        return all_tasks

    @log_and_propagate_error_on_service_method
    def get_agent_task_by_agent_id_and_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
    ) -> AgentTask:
        """Returns a specific task belonging to a specific agent.

        Args:
            agent_id: The ID of the agent that owns the task.
            task_id: The ID of the task to retrieve.

        Returns:
            The requested task.

        Raises:
            AgentNotFoundError: If no agent with the given agent ID is registered.
            AgentTaskNotFoundError: If the agent has no task with the given task ID.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        task = agent.get_task_by_task_id(task_id=task_id)
        self._logger.debug(
            "Retrieved task {} from agent {}",
            task_id,
            agent,
        )
        return task

    @log_and_propagate_error_on_service_method
    async def task_agent_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        command: str,
        arguments: dict[str, Any],
    ) -> AgentTask:
        """Queues a command for execution on the specified agent and emits an `AGENT_TASKED` event.

        Args:
            agent_id: The ID of the agent to task.
            command: The name of the command to execute on the agent.
            arguments: The arguments to pass along with the command.

        Returns:
            The newly created task object representing the queued command.

        Raises:
            AgentNotFoundError: If no agent with the given ID is registered.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)

        task = AgentTask(command=command, arguments=arguments)
        await agent.submit_task(task=task)

        await self._events_service.trigger_event(
            event_type=EventType.AGENT_TASKED,
            message=f"Tasked agent: {agent}",
            data={
                "agent_id": str(agent.agent_id),
                "task": task.to_json(),
            },
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
            asyncio.create_task(
                self._events_service.trigger_event(
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

    @log_and_propagate_error_on_service_method
    def delete_queued_agent_task_by_agent_id_and_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
    ):
        """Deletes a queued (not yet dispatched) task from the specified agent's task queue.

        Args:
            agent_id: The ID of the agent that owns the task.
            task_id: The ID of the queued task to delete.

        Returns:
            None

        Raises:
            AgentNotFoundError: If no agent with the given agent ID is registered.
            AgentTaskNotFoundError: If the agent has no queued task with the given
                task ID.
        """
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        agent.delete_queued_task_by_task_id(task_id=task_id)
