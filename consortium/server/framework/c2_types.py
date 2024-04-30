import uuid


class AgentType:
    def __init__(
        self,
        name: str = "",
        # "ListenerType" is not defined yet at this point, so we use a string instead in
        # the type hint
        compatible_listener_types: list["ListenerType"] | None = None,
    ):
        self.name = name
        self.compatible_listener_types = set()
        if compatible_listener_types is None:
            compatible_listener_types = []
        for listener_type in compatible_listener_types:
            if not isinstance(listener_type, ListenerType):
                raise ValueError(
                    f"Invalid listener type {listener_type} provided, expected an "
                    f"instance of ListenerType",
                )
            self.compatible_listener_types.add(listener_type)
            if self not in listener_type.compatible_agent_types:
                listener_type.add_compatible_agent_type(self)

        self.agent_type_id = uuid.uuid4()

    def add_compatible_listener_type(self, listener_type: "ListenerType") -> None:
        if not isinstance(listener_type, ListenerType):
            raise ValueError(
                f"Invalid listener type {listener_type} provided, expected an instance "
                f"of ListenerType",
            )
        if listener_type in self.compatible_listener_types:
            raise ValueError(
                f"Listener type {listener_type} is already in the set of compatible "
                f"listener types",
            )
        self.compatible_listener_types.add(listener_type)
        # Prevent infinite recursion
        if self not in listener_type.compatible_agent_types:
            listener_type.add_compatible_agent_type(self)

    def remove_compatible_listener_type(self, listener_type: "ListenerType") -> None:
        if not isinstance(listener_type, ListenerType):
            raise ValueError(
                f"Invalid listener type {listener_type} provided, expected an instance "
                f"of ListenerType",
            )
        if listener_type not in self.compatible_listener_types:
            raise ValueError(
                f"Listener type {listener_type} is not in the set of compatible "
                f"listener types",
            )
        self.compatible_listener_types.remove(listener_type)
        listener_type.remove_compatible_agent_type(self)

    def is_compatible_with_listener_type(self, listener_type: "ListenerType") -> bool:
        # if compatible_listener_types is set to None, then the agent is compatible with
        # all listener types
        if self.compatible_listener_types is None:
            return True
        return listener_type in self.compatible_listener_types

    def to_json(self) -> dict[str, str]:
        return {
            "name": self.name,
            "compatible_listener_type_ids": [
                str(listener_type.listener_type_id)
                for listener_type in self.compatible_listener_types
            ],
            "agent_type_id": str(self.agent_type_id),
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.agent_type_id)})'

    def __repr__(self) -> str:
        return (
            f"AgentType(name={self.name!r}, "
            f"compatible_listener_types={self.compatible_listener_types!r})"
        )


class ListenerType:
    def __init__(
        self,
        name: str = "",
        compatible_agent_types: list[AgentType] | None = None,
    ):
        self.name = name
        self.compatible_agent_types = set()
        if compatible_agent_types is None:
            compatible_agent_types = []
        for agent_type in compatible_agent_types:
            if not isinstance(agent_type, AgentType):
                raise ValueError(
                    f"Invalid agent type {agent_type} provided, expected an instance "
                    f"of AgentType",
                )
            self.compatible_agent_types.add(agent_type)
            if self not in agent_type.compatible_listener_types:
                agent_type.add_compatible_listener_type(self)

        self.listener_type_id = uuid.uuid4()

    def add_compatible_agent_type(self, agent_type: AgentType) -> None:
        if not isinstance(agent_type, AgentType):
            raise ValueError(
                f"Invalid agent type {agent_type} provided, expected an instance of "
                f"AgentType",
            )
        if agent_type in self.compatible_agent_types:
            raise ValueError(
                f"Agent type {agent_type} is already in the set of compatible agent "
                f"types",
            )
        self.compatible_agent_types.add(agent_type)
        # Prevent infinite recursion
        if self not in agent_type.compatible_listener_types:
            agent_type.add_compatible_listener_type(self)

    def remove_compatible_agent_type(self, agent_type: AgentType) -> None:
        if not isinstance(agent_type, AgentType):
            raise ValueError(
                f"Invalid agent type {agent_type} provided, expected an instance of "
                f"AgentType",
            )
        if agent_type not in self.compatible_agent_types:
            raise ValueError(
                f"Agent type {agent_type} is not in the set of compatible agent types",
            )
        self.compatible_agent_types.remove(agent_type)
        agent_type.remove_compatible_listener_type(self)

    def is_compatible_with_agent_type(self, agent_type: AgentType) -> bool:
        # if compatible_agent_types is set to None, then the listener is compatible with
        # all agent types
        if self.compatible_agent_types is None:
            return True
        return agent_type in self.compatible_agent_types

    def to_json(self) -> dict[str, str]:
        return {
            "name": self.name,
            "compatible_agent_type_ids": [
                str(agent_type.agent_type_id)
                for agent_type in self.compatible_agent_types
            ],
            "listener_type_id": str(self.listener_type_id),
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.listener_type_id)})'

    def __repr__(self) -> str:
        return (
            f"ListenerType(name={self.name!r}, "
            f"compatible_agent_types={self.compatible_agent_types!r})"
        )
