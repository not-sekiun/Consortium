import uuid
from typing import Any

from loguru import logger

from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions import (
    AgentNotFoundError,
)
from consortium.server.objects.agent_objects import Agent
from consortium.server.server_logging import LoggerType
from consortium.server.utils import log_and_propagate_error_on_service_method


class ConnectedAgentsService:
    def __init__(self):
        # Importing here to avoid circular imports.
        from consortium.server import server_singletons as server_singletons

        self._agents_service = server_singletons.agents_service
        self._agents = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self) -> str:
        return "Connected Agents Service"

    def __repr__(self) -> str:
        return "ConnectedAgentsService()"

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
        """
        Register a new connected agent with the listener.

        Args:
            payload_id (str | None): The payload ID of the payload that the agent is
                using to connect to the listener.
            agent_type (BaseAgentType): The agent type of the agent to be registered.
            name (str): The human-readable name of the agent.
            description (str): A description of the agent.
            endpoint (str): A human-readable representation of the network endpoint that
                uniquely identifies the agent. This is typically the socket address of
                the agent.
            is_admin (bool | None): A boolean that indicates whether the agent is
                running with administrator/superuser privileges.
            os (str | None): The operating system of the agent.
            version (str | None): The version of the operating system that the agent is
                running on.
            arch (str | None): The architecture of the system that the agent is running
                on.
            pid (int | None): The process ID of the agent.
            locale (str | None): The locale of the system that the agent is running on.
            remote_host_address (str | None): The remote host address of the agent.
            local_host_address (str | None): The local host address of the agent.
            hostname (str | None): The hostname of the system that the agent is running
                on.
            agent_data (dict[str, Any] | None): A dictionary of any additional data that
                the agent may send to the listener.

        Returns:
            Agent: An object representing the agent that was registered.
        """

        agent = self._agents_service.register_agent(
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
        return agent

    @log_and_propagate_error_on_service_method
    def check_in_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        """
        Check in a connected agent by its agent ID. This method simply updates the last
        check-in time of the agent to indicate that the agent is still connected and
        has called back.

        Args:
            agent_id (str): The agent ID of the agent to check in. This should be a
                UUID4 string.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.

        Returns:
            None
        """

        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id=agent_id)
        self._agents_service.check_in_agent_by_agent_id(agent_id=agent_id)

    @log_and_propagate_error_on_service_method
    def deregister_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        """
        Deregister a connected agent by its agent ID. This method removes the agent from
        the listener's list of connected agents and also removes the agent from the
        database. This effectively marks an agent as disconnected.

        Args:
            agent_id (str): The agent ID of the agent to deregister. This should be a
                UUID4 string.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found.

        Returns:
            None
        """

        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id=agent_id)
        self._agents_service.deregister_agent_by_agent_id(agent_id=agent_id)
        self._agents.pop(str(agent_id))

    @log_and_propagate_error_on_service_method
    def get_all_agents(self) -> list[Agent]:
        """
        Get all connected agents that are registered with the specific listener that is
        using this agent manager.

        Returns:
            list[Agent]: A list of all connected agents that are registered with the
                specific listener that is using this agent manager.
        """

        return list(self._agents.values())

    @log_and_propagate_error_on_service_method
    def get_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> Agent:
        """
        Get a connected agent by its agent ID for the specific listener that is using
        this agent manager.

        Args:
            agent_id (str): The agent ID of the agent to get. This should be a UUID4
                string.

        Raises:
            AgentNotFoundError: Raised if the agent with the specified agent ID is not
                found

        Returns:
            Agent: The agent with the specified agent ID.
        """
        agent_id = str(agent_id)

        try:
            return self._agents[agent_id]
        except KeyError:
            raise AgentNotFoundError(agent_id=agent_id) from None
