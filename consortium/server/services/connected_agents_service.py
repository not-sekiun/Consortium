import uuid
from collections.abc import AsyncGenerator, AsyncIterable
from typing import TYPE_CHECKING, Any

from loguru import logger

from consortium.framework.agents.agent_message_models import (
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
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
        remote_ip: str | None = None,
        local_ip: str | None = None,
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
            remote_ip: The remote host address of the agent.
            local_ip: The local host address of the agent.
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
            remote_ip=remote_ip,
            local_ip=local_ip,
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
    async def get_next_task_message_by_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
        timeout: float | None = None,
    ) -> TaskInputMessageModel | TaskOutputMessageModel | None:
        """Get the next task message produced by a running capability for a specific task
        on an agent connected to this listener.

        Args:
            agent_id: The agent ID of the agent to read the task message from.
            task_id: The task ID of the running task whose next message to read.
            timeout: Maximum time in seconds to wait for the next message. If None, waits
                indefinitely. If 0, polls without blocking.

        Returns:
            The next task message produced by the task's capability, or None if the
            capability has finished (end of stream) or the timeout elapsed before a
            message was produced.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
            AgentTaskNotFoundError: Raised if the task with the specified task ID is not
                found on the agent.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        return await self._agents_service.get_next_task_message_by_task_id(
            agent_id=agent_id,
            task_id=task_id,
            timeout=timeout,
        )

    @log_and_propagate_error_on_service_method
    async def get_next_task_message_sequential(
        self,
        agent_id: str | uuid.UUID,
        timeout: float | None = None,
    ) -> TaskInputMessageModel | TaskOutputMessageModel | None:
        """Get the next task message from the earliest running capability of an agent
        connected to this listener.

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
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        return await self._agents_service.get_next_task_message_sequential(
            agent_id=agent_id,
            timeout=timeout,
        )

    @log_and_propagate_error_on_service_method
    async def get_next_task_message_any(
        self,
        agent_id: str | uuid.UUID,
        timeout: float | None = None,
    ) -> TaskLaunchMessageModel | TaskOutputMessageModel | None:
        """Get the next task message from any running capability of an agent connected to
        this listener.

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
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        return await self._agents_service.get_next_task_message_any(
            agent_id=agent_id,
            timeout=timeout,
        )

    async def drain_task_messages_by_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Drain task messages from a specific running task of an agent connected to this
        listener until it completes.

        Yields each message produced by the task's capability in order, terminating when
        the capability finishes.

        Args:
            agent_id: The agent ID of the agent to drain task messages from.
            task_id: The task ID of the running task whose messages to drain.

        Yields:
            Each task message produced by the task's capability, in the order produced.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
            AgentTaskNotFoundError: Raised if the task with the specified task ID is not
                found on the agent.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        async for task_message in self._agents_service.drain_task_messages_by_task_id(
            agent_id=agent_id,
            task_id=task_id,
        ):
            yield task_message

    async def drain_task_messages_sequential(
        self,
        agent_id: str | uuid.UUID,
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Drain task messages from an agent connected to this listener one capability at
        a time.

        Yields messages from the earliest started capability until it completes before
        moving on to the next one, preserving a strict per-capability ordering. Loops
        indefinitely, waiting for new capabilities to start as needed.

        Args:
            agent_id: The agent ID of the agent to drain task messages from.

        Yields:
            Each task message, drained from the earliest running capability first.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        async for task_message in self._agents_service.drain_task_messages_sequential(
            agent_id=agent_id,
        ):
            yield task_message

    async def drain_task_messages_any(
        self,
        agent_id: str | uuid.UUID,
    ) -> AsyncGenerator[TaskLaunchMessageModel | TaskInputMessageModel]:
        """Drain task messages from any running capability of an agent connected to this
        listener.

        Yields messages from any running capability, interleaving (muxing) them in the
        order they become available. Loops indefinitely, waiting for new capabilities to
        start as needed.

        Args:
            agent_id: The agent ID of the agent to drain task messages from.

        Yields:
            Each task message, in the order it becomes available across all running
            capabilities.

        Raises:
            AgentNotFoundError: Raised if the agent does not exist or is not connected
                to this listener.
        """
        self._validate_agent_connected_to_listener(agent_id=agent_id)
        async for task_message in self._agents_service.drain_task_messages_any(
            agent_id=agent_id,
        ):
            yield task_message

    @log_and_propagate_error_on_service_method
    async def dispatch_task_output_message(
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
        await self._agents_service.dispatch_task_output_message(
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
