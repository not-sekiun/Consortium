import sys
import uuid

from consortium.server.exceptions.framework_exceptions.c2_types_framework_exceptions import (
    AgentTypeAlreadyExistsError,
    AgentTypeConfigurationError,
    AgentTypeConfigurationParameterTypeError,
    AgentTypeNotFoundError,
    EmptyListenerTypeNameError,
    ListenerTypeAlreadyExistsError,
    ListenerTypeConfigurationParameterTypeError,
    ListenerTypeNotFoundError,
)


class AgentType:
    def __init__(
        self,
        name: str,
        # `ListenerType` is not defined yet at this point, so we use a forward
        # reference.
        compatible_listener_types: set["ListenerType"] | None = None,
    ):
        if compatible_listener_types is None:
            compatible_listener_types = set()

        if not isinstance(name, str):
            raise AgentTypeConfigurationError("The agent type's name must be a string.")
        if not name:
            raise AgentTypeConfigurationError(
                "The agent type's name must not be an empty string.",
            )
        if not isinstance(compatible_listener_types, set):
            raise AgentTypeConfigurationError(
                "The agent type's provided compatible listener types must be a set.",
            )
        for listener_type in compatible_listener_types:
            if not isinstance(listener_type, ListenerType):
                raise AgentTypeConfigurationError(
                    "The elements in the set of compatible listener types must be "
                    "listener type objects.",
                )

        self.name = name
        self.compatible_listener_types = set()
        self.agent_type_id = uuid.uuid4()

        for listener_type in compatible_listener_types:
            self.add_compatible_listener_type(listener_type=listener_type)

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.agent_type_id)})'

    def __repr__(self) -> str:
        return (
            f"AgentType(name={self.name!r}, "
            f"compatible_listener_types={self.compatible_listener_types!r})"
        )

    def add_compatible_listener_type(self, listener_type: "ListenerType") -> None:
        if not isinstance(listener_type, ListenerType):
            raise ListenerTypeConfigurationParameterTypeError(
                error_message=(
                    "Invalid listener type '{listener_type}' provided, expected a "
                    "listener type object."
                ),
            )
        if listener_type in self.compatible_listener_types:
            raise ListenerTypeAlreadyExistsError(
                listener_type=listener_type,
                agent_type=self,
            )
        self.compatible_listener_types.add(listener_type)
        listener_type.compatible_agent_types.add(self)

    def remove_compatible_listener_type(self, listener_type: "ListenerType") -> None:
        if not isinstance(listener_type, ListenerType):
            raise AgentTypeConfigurationParameterTypeError(
                error_message=(
                    f"Invalid listener type '{listener_type}' provided, expected a "
                    "listener type object."
                ),
            )
        if listener_type not in self.compatible_listener_types:
            raise ListenerTypeNotFoundError(
                listener_type=listener_type,
                agent_type=self,
            )
        self.compatible_listener_types.remove(listener_type)
        listener_type.compatible_agent_types.remove(self)

    def is_compatible_with_listener_type(self, listener_type: "ListenerType") -> bool:
        # If `compatible_listener_types` is set to `None`, then the agent is compatible
        # with all listener types.
        if self.compatible_listener_types is None:
            return True
        return listener_type in self.compatible_listener_types

    def to_json(self) -> dict[str, str]:
        return {
            "name": self.name,
            "compatible_listener_types": [
                {
                    "name": listener_type.name,
                    "listener_type_id": str(listener_type.listener_type_id),
                }
                for listener_type in self.compatible_listener_types
            ],
            "agent_type_id": str(self.agent_type_id),
        }


class ListenerType:
    def __init__(
        self,
        name: str = "",
        compatible_agent_types: set[AgentType] | None = None,
    ):
        if compatible_agent_types is None:
            compatible_agent_types = set()

        if not isinstance(name, str):
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[self.__class__.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not name:
            raise EmptyListenerTypeNameError
        if not isinstance(compatible_agent_types, set):
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[self.__class__.__module__].__file__,
                parameter_name="compatible_agent_types",
                parameter_type="set",
            )
        for agent_type in compatible_agent_types:
            if not isinstance(agent_type, AgentType):
                raise ListenerTypeConfigurationParameterTypeError(
                    listener_type_filepath=sys.modules[
                        self.__class__.__module__
                    ].__file__,
                    error_message=(
                        "The elements in the set of compatible agent types must be "
                        "agent type objects."
                    ),
                )

        self.name = name
        self.compatible_agent_types = set()
        self.listener_type_id = uuid.uuid4()

        for agent_type in compatible_agent_types:
            self.add_compatible_agent_type(agent_type=agent_type)

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.listener_type_id)})'

    def __repr__(self) -> str:
        return (
            f"ListenerType(name={self.name!r}, "
            f"compatible_agent_types={self.compatible_agent_types!r})"
        )

    def add_compatible_agent_type(self, agent_type: AgentType) -> None:
        if not isinstance(agent_type, AgentType):
            raise ValueError(
                f"Invalid agent type '{agent_type}' provided, expected an agent type "
                "object.",
            )
        if agent_type in self.compatible_agent_types:
            raise AgentTypeAlreadyExistsError(
                agent_type=agent_type,
                listener_type=self,
            )
        self.compatible_agent_types.add(agent_type)
        agent_type.compatible_listener_types.add(self)

    def remove_compatible_agent_type(self, agent_type: AgentType) -> None:
        if not isinstance(agent_type, AgentType):
            raise ValueError(
                f"Invalid agent type '{agent_type}' provided, expected an agent type "
                "object",
            )
        if agent_type not in self.compatible_agent_types:
            raise AgentTypeNotFoundError(
                agent_type=agent_type,
                listener_type=self,
            )
        self.compatible_agent_types.remove(agent_type)
        agent_type.compatible_listener_types.remove(self)

    def is_compatible_with_agent_type(self, agent_type: AgentType) -> bool:
        # If `compatible_agent_types` is set to `None`, then the listener is compatible
        # with all agent types.
        if self.compatible_agent_types is None:
            return True
        return agent_type in self.compatible_agent_types

    def to_json(self) -> dict[str, str]:
        return {
            "name": self.name,
            "compatible_agent_types": [
                {
                    "name": agent_type.name,
                    "agent_type_id": str(agent_type.agent_type_id),
                }
                for agent_type in self.compatible_agent_types
            ],
            "listener_type_id": str(self.listener_type_id),
        }
