import uuid
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

from loguru import logger

from consortium.framework.agents.agent_message_models import TaskLaunchMessageModel
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
)

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent


class ConnectedAgentsService:
    """A thin service wrapper around AgentsService that provides listener-scoped agent
    operations. This service ensures that all agent operations are validated against
    the listener that owns this service instance, and automatically handles agent
    check-ins where appropriate.

    This service is intended to be used by listeners to interact with agents that are
    connected to them. It provides a higher-level abstraction over the AgentsService
    that simplifies common listener operations like retrieving tasks and submitting
    results.
    """

    def __init__(self, listener_id: uuid.UUID):
        # Importing here to avoid circular imports.
        import consortium.server.server_singletons as server_singletons

        self._listener_id = listener_id
        self._agents_service = server_singletons.agents_service
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self) -> str:
        return "Connected Agents Service"

    def __repr__(self) -> str:
        return "ConnectedAgentsService()"

    def _validate_agent_connected_to_listener(self, agent_id: str | uuid.UUID) -> Agent:
        agent = self._agents_service.get_agent_by_agent_id(agent_id=agent_id)
        connected_listener = agent.connected_listener
        if (
            connected_listener is None
            or connected_listener.listener_id != self._listener_id
        ):
            raise AgentNotFoundError(agent_id=agent.agent_id)
        return agent

    @log_and_propagate_error_on_service_method
    def register_agent(
        self,
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
        """Register a new agent with this listener.

        Args:
            payload_id: The payload ID of the payload that the agent is using to
                connect to the listener.
            agent_type: The agent type of the agent to be registered.
            name: The human-readable name of the agent.
            description: A description of the agent.
            endpoint: A human-readable representation of the network endpoint that
                uniquely identifies the agent.
            user: The name of the user account that the agent is running on.
            is_admin: Whether the agent is running with administrator privileges.
            os: The operating system of the agent.
            version: The version of the operating system.
            arch: The architecture of the system.
            pid: The process ID of the agent.
            locale: The locale of the system.
            remote_host_address: The remote host address of the agent.
            local_host_address: The local host address of the agent.
            hostname: The hostname of the system.
            agent_data: Additional data from the agent.

        Raises:
            AgentTypeResolutionError: Raised if the agent type cannot be resolved from
                the provided payload_id or agent_type.
            AgentCreationParameterTypeError: Raised if a parameter has an invalid type.

        Returns:
            The registered agent object.
        """
        return self._agents_service.register_agent(
            listener_id=self._listener_id,
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

    @log_and_propagate_error_on_service_method
    def deregister_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        """Deregister an agent connected to this listener. This removes the agent from
        the system entirely.

        Args:
            agent_id: The agent ID of the agent to deregister.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        self._agents_service.deregister_agent_by_agent_id(agent_id=agent_id)

    @log_and_propagate_error_on_service_method
    def check_in_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        """Check in an agent connected to this listener. This updates the agent's last
        check-in time and marks it as active.

        Args:
            agent_id: The agent ID of the agent to check in.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        self._agents_service.check_in_agent_by_agent_id(agent_id=agent_id)

    @log_and_propagate_error_on_service_method
    async def get_next_agent_task_messages_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        count: int | None = None,
        block: bool = False,
        timeout: float | None = None,
    ) -> list[TaskLaunchMessageModel]:
        """Get pending tasks for an agent connected to this listener. This method also
        performs an automatic check-in for the agent.

        Args:
            agent_id: The agent ID of the agent to get tasks for.
            count: The number of tasks to retrieve. If None, retrieves all available
                tasks. If 1, retrieves a single task. If > 1, retrieves up to that
                many tasks.
            block: If True, blocks until at least one task is available.
                If False, returns immediately with whatever tasks are available
                (may be empty). Defaults to False.
            timeout: Maximum time in seconds to block waiting for tasks. Only applies
                when block=True. If None, blocks indefinitely. If 0, equivalent to
                block=False.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.

        Returns:
            A list of task message objects, or an empty list if none are available.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        self._agents_service.check_in_agent_by_agent_id(agent_id=agent_id)
        return await self._agents_service.get_next_agent_task_messages_by_agent_id(
            agent_id=agent_id,
            count=count,
            block=block,
            timeout=timeout,
        )

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
        """Submit a result from an agent connected to this listener. This method validates
        that the task exists and is running, performs an automatic check-in, and
        submits the result.

        Args:
            agent_id: The agent ID of the agent submitting the result.
            task_id: The task ID that this result corresponds to.
            success: Whether the task was successful.
            message: A message describing the result.
            data: The result data.
            payload: An optional binary payload associated with the result.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
            AgentTaskNotFoundError: Raised if the task ID does not correspond to a
                running task for this agent.
        """
        agent = self._validate_agent_connected_to_listener(agent_id=agent_id)
        # Validate the task ID corresponds to a running task before submitting
        _ = agent.get_running_task_by_task_id(task_id=task_id)
        self._agents_service.check_in_agent_by_agent_id(agent_id=agent_id)
        await self._agents_service.submit_result_by_agent_id(
            agent_id=agent_id,
            task_id=task_id,
            success=success,
            message=message,
            data=data,
            payload=payload,
        )

    @log_and_propagate_error_on_service_method
    def get_all_agents(self) -> list[Agent]:
        """Get all agents connected to this listener.

        Returns:
            A list of all agents connected to this listener.
        """
        all_agents = self._agents_service.get_all_agents()
        connected_agents = []
        for agent in all_agents:
            connected_listener = agent.connected_listener
            if (
                connected_listener is not None
                and connected_listener.listener_id == self._listener_id
            ):
                connected_agents.append(agent)
        return connected_agents

    @log_and_propagate_error_on_service_method
    def get_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> Agent:
        """Get an agent by its agent ID, validating it is connected to this listener.

        Args:
            agent_id: The agent ID of the agent to retrieve.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.

        Returns:
            The agent with the specified agent ID.
        """
        return self._validate_agent_connected_to_listener(agent_id=agent_id)
