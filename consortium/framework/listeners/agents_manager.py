from typing import Any

from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.exceptions.listeners_framework_exceptions import (
    ListenerSpecificAgentNotFoundError,
)
from consortium.server import server_singletons as server_singletons
from consortium.framework.agents.agent import Agent


class AgentsManager:
    """
    A class that allows listeners to manage the lifetime of an agent from registration
    to checking in to deregistration, as well as to manage access to agents registered
    locally to the specific listener.
    """

    def __init__(self):
        self._agents_service = server_singletons.agents_service
        self._agents = {}

    async def register_new_connected_agent(
        self,
        agent_type: BaseAgentType,
        name: str = "",
        description: str = "",
        endpoint: str = "",
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

        agent = await self._agents_service.create_and_add_agent(
            agent_type=agent_type,
            name=name,
            description=description,
            endpoint=endpoint,
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

    async def check_in_connected_agent_by_agent_id(self, agent_id: str) -> None:
        """
        Check in a connected agent by its agent ID. This method simply updates the last
        check-in time of the agent to indicate that the agent is still connected and
        has called back.

        Args:
            agent_id (str): The agent ID of the agent to check in. This should be a
                UUID4 string.

        Raises:
            ListenerSpecificAgentNotFoundError: Raised if the agent with the specified
                agent ID is not found.

        Returns:
            None
        """

        if agent_id not in self._agents:
            raise ListenerSpecificAgentNotFoundError(agent_id=agent_id)
        await self._agents_service.check_in_agent_by_agent_id(agent_id=agent_id)

    async def deregister_connected_agent_by_agent_id(self, agent_id: str) -> None:
        """
        Deregister a connected agent by its agent ID. This method removes the agent from
        the listener's list of connected agents and also removes the agent from the
        database. This effectively marks an agent as disconnected.

        Args:
            agent_id (str): The agent ID of the agent to deregister. This should be a
                UUID4 string.

        Raises:
            ListenerSpecificAgentNotFoundError: Raised if the agent with the specified
                agent ID is not found.

        Returns:
            None
        """

        if agent_id not in self._agents:
            raise ListenerSpecificAgentNotFoundError(agent_id=agent_id)
        await self._agents_service.remove_agent_by_agent_id(agent_id=agent_id)
        self._agents.pop(str(agent_id))

    def get_all_connected_agents(self) -> list[Agent]:
        """
        Get all connected agents that are registered with the specific listener that is
        using this agent manager.

        Returns:
            list[Agent]: A list of all connected agents that are registered with the
                specific listener that is using this agent manager.
        """

        return list(self._agents.values())

    def get_connected_agent_by_agent_id(self, agent_id: str) -> Agent:
        """
        Get a connected agent by its agent ID for the specific listener that is using
        this agent manager.

        Args:
            agent_id (str): The agent ID of the agent to get. This should be a UUID4
                string.

        Raises:
            ListenerSpecificAgentNotFoundError: Raised if the agent with the specified

        Returns:
            Agent: The agent with the specified agent ID.
        """

        try:
            return self._agents[agent_id]
        except KeyError:
            raise ListenerSpecificAgentNotFoundError(agent_id=agent_id)
