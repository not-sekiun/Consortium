import asyncio
import uuid
from collections.abc import AsyncIterable
from datetime import datetime
from typing import Any

from loguru import logger

from consortium.framework.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions import (
    AgentNotFoundError,
    AgentTaskNotFoundError,
)
from consortium.server.models.agent_task_models import (
    AgentTaskState,
)
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.agent_task_objects import AgentTask
from consortium.server.server_logging import LoggerType
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
        """
        Get pending task messages for an agent. This method retrieves task messages
        that are queued for the agent and returns them as a list of
        `AgentTaskMessageModel` objects.

        Args:
            agent_id (str | uuid.UUID): The agent ID of the agent to get tasks for.
            count (int | None): The number of tasks to retrieve. If None, retrieves
                all available tasks. If 1, retrieves a single task. If > 1, retrieves
                up to that many tasks.
            block (bool): If True, blocks until at least one task is available.
                If False, returns immediately with whatever tasks are available
                (may be empty). Defaults to False.
            timeout (float | None): Maximum time in seconds to block waiting for tasks.
                Only applies when block=True. If None, blocks indefinitely.
                If 0, equivalent to block=False.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.

        Returns:
            list[TaskLaunchMessageModel]: A list of task messages. Returns an empty list
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
        """
        Submit a result for a running task on an agent.

        Args:
            agent_id (str | uuid.UUID): The agent ID of the agent to submit the result
                for.
            task_id (str | uuid.UUID): The task ID of the task to submit the result for.
            success (bool): Whether the task was successful.
            message (str): A message describing the result.
            data (dict[str, Any]): The result data.
            payload (AsyncIterable[bytes] | bytes | None): Optional binary payload
                associated with the result.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.
            AgentResultHasNoCorrespondingTaskError: Raised if the task ID does not
                correspond to a running task for this agent.

        Returns:
            None
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
        agent_id = normalize_uuid(value=agent_id)

        try:
            agent = self._agents[agent_id]
        except KeyError:
            raise AgentNotFoundError(agent_id=agent_id) from None

        self._logger.debug("Retrieved agent: {!r}", agent)
        return agent

    @log_and_propagate_error_on_service_method
    def get_all_agents(self) -> list[Agent]:
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
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        agent.delete_queued_task_by_task_id(task_id=task_id)
