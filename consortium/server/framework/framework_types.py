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
                    f"Invalid listener type {listener_type} provided, expected an instance of ListenerType",
                )
            self.compatible_listener_types.add(listener_type)

        self.agent_type_id = uuid.uuid4()

    def add_compatible_listener_type(self, listener_type: "ListenerType") -> None:
        if not isinstance(listener_type, ListenerType):
            raise ValueError(
                f"Invalid listener type {listener_type} provided, expected an instance of ListenerType",
            )
        if listener_type in self.compatible_listener_types:
            raise ValueError(
                f"Listener type {listener_type} is already in the list of compatible listener types",
            )
        self.compatible_listener_types.add(listener_type)
        listener_type.add_compatible_agent_type(self)

    def remove_compatible_listener_type(self, listener_type: "ListenerType") -> None:
        if not isinstance(listener_type, ListenerType):
            raise ValueError(
                f"Invalid listener type {listener_type} provided, expected an instance of ListenerType",
            )
        if listener_type not in self.compatible_listener_types:
            raise ValueError(
                f"Listener type {listener_type} is not in the list of compatible listener types",
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
            "compatible_listener_types": (
                [
                    str(listener_type.listener_type_id)
                    for listener_type in self.compatible_listener_types
                ]
                if self.compatible_listener_types
                else None
            ),
            "agent_type_id": str(self.agent_type_id),
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.agent_type_id)})'

    def __repr__(self) -> str:
        return f"AgentType(name={self.name!r}, compatible_listener_types={self.compatible_listener_types!r})"


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
                    f"Invalid agent type {agent_type} provided, expected an instance of AgentType",
                )
            self.compatible_agent_types.add(agent_type)

        self.listener_type_id = uuid.uuid4()

    def add_compatible_agent_type(self, agent_type: AgentType) -> None:
        if not isinstance(agent_type, AgentType):
            raise ValueError(
                f"Invalid agent type {agent_type} provided, expected an instance of AgentType",
            )
        if agent_type in self.compatible_agent_types:
            raise ValueError(
                f"Agent type {agent_type} is already in the list of compatible agent types",
            )
        self.compatible_agent_types.add(agent_type)
        agent_type.add_compatible_listener_type(self)

    def remove_compatible_agent_type(self, agent_type: AgentType) -> None:
        if not isinstance(agent_type, AgentType):
            raise ValueError(
                f"Invalid agent type {agent_type} provided, expected an instance of AgentType",
            )
        if agent_type not in self.compatible_agent_types:
            raise ValueError(
                f"Agent type {agent_type} is not in the list of compatible agent types",
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
            "compatible_agent_types": (
                [
                    str(agent_type.agent_type_id)
                    for agent_type in self.compatible_agent_types
                ]
                if self.compatible_agent_types
                else None
            ),
            "listener_type_id": str(self.listener_type_id),
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.listener_type_id)})'

    def __repr__(self) -> str:
        return f"ListenerType(name={self.name!r}, compatible_agent_types={self.compatible_agent_types!r})"
