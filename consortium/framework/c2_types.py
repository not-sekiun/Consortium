import sys
import uuid
from pathlib import Path

from consortium.framework.base_agent_capability import BaseAgentCapability
from consortium.server.exceptions.framework_exceptions.c2_types_framework_exceptions import (
    AgentTypeAlreadyExistsError,
    AgentTypeConfigurationError,
    AgentTypeConfigurationParameterTypeError,
    AgentTypeNotFoundError,
    EmptyAgentTypeNameError,
    EmptyListenerTypeNameError,
    ListenerTypeAlreadyExistsError,
    ListenerTypeConfigurationParameterTypeError,
    ListenerTypeNotFoundError,
)


class BaseAgentType:
    name: str
    compatible_listener_types: set["BaseListenerType"] | None = None
    agent_capabilities: set[BaseAgentCapability] | None = None

    def __init__(self):
        self.agent_type_id = uuid.uuid4()
        self.agent_source_filepath = Path(
            sys.modules[self.__class__.__module__].__file__,
        ).parents[0]

        for listener_type in self.compatible_listener_types:
            if listener_type not in self.compatible_listener_types:
                self.add_compatible_listener_type(listener_type=listener_type)

    def __init_subclass__(cls, **kwargs):
        if cls.compatible_listener_types is None:
            cls.compatible_listener_types = set()
        if cls.agent_capabilities is None:
            cls.agent_capabilities = set()

        if not isinstance(cls.name, str):
            raise AgentTypeConfigurationError("The agent type's name must be a string.")
        if not cls.name:
            raise EmptyAgentTypeNameError
        if not isinstance(cls.compatible_listener_types, set):
            raise AgentTypeConfigurationParameterTypeError(
                agent_type_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="compatible_listener_types",
                parameter_type="set",
            )
        for listener_type in cls.compatible_listener_types:
            if not isinstance(listener_type, BaseListenerType):
                raise AgentTypeConfigurationParameterTypeError(
                    agent_type_filepath=sys.modules[cls.__module__].__file__,
                    error_message=(
                        "The elements in the set of compatible listener types must be "
                        "listener type objects."
                    ),
                )
        if not isinstance(cls.agent_capabilities, set):
            raise AgentTypeConfigurationParameterTypeError(
                agent_type_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="agent_capabilities",
                parameter_type="set",
            )
        for agent_capability in cls.agent_capabilities:
            if not isinstance(agent_capability, BaseAgentCapability):
                raise AgentTypeConfigurationParameterTypeError(
                    agent_type_filepath=sys.modules[cls.__module__].__file__,
                    error_message=(
                        "The elements in the set of agent capabilities must be "
                        "agent capability objects."
                    ),
                )

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.agent_type_id)})'

    def __repr__(self) -> str:
        return (
            f"AgentType(name={self.name!r}, "
            f"compatible_listener_types={self.compatible_listener_types!r})"
        )

    def add_compatible_listener_type(self, listener_type: "BaseListenerType") -> None:
        if not isinstance(listener_type, BaseListenerType):
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[self.__class__.__module__].__file__,
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

    def remove_compatible_listener_type(
        self,
        listener_type: "BaseListenerType",
    ) -> None:
        if not isinstance(listener_type, BaseListenerType):
            raise AgentTypeConfigurationParameterTypeError(
                agent_type_filepath=sys.modules[self.__class__.__module__].__file__,
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

    def is_compatible_with_listener_type(
        self,
        listener_type: "BaseListenerType",
    ) -> bool:
        # If `compatible_listener_types` is set to `None`, then the agent is compatible
        # with all listener types.
        if self.compatible_listener_types is None:
            return True
        return listener_type in self.compatible_listener_types

    def get_all_compatible_listener_types(self) -> dict[str, "BaseListenerType"]:
        return {
            str(listener_type.listener_type_id): listener_type
            for listener_type in self.compatible_listener_types
        }

    def get_compatible_listener_type_by_listener_type_id(
        self,
        listener_type_id: str,
    ) -> "BaseListenerType":
        for listener_type in self.compatible_listener_types:
            if str(listener_type.listener_type_id) == listener_type_id:
                return listener_type
        raise ListenerTypeNotFoundError

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
            "agent_capabilities": {
                agent_capability.name: agent_capability.to_json()
                for agent_capability in self.agent_capabilities
            },
        }


class BaseListenerType:
    name: str
    compatible_agent_types: set[BaseAgentType] | None = None

    def __init__(
        self,
    ):
        self.listener_type_id = uuid.uuid4()

        for agent_type in self.compatible_agent_types:
            if agent_type not in self.compatible_agent_types:
                self.add_compatible_agent_type(agent_type=agent_type)

    def __init_subclass__(cls, **kwargs):
        if cls.compatible_agent_types is None:
            cls.compatible_agent_types = set()

        if not isinstance(cls.name, str):
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not cls.name:
            raise EmptyListenerTypeNameError
        if not isinstance(cls.compatible_agent_types, set):
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="compatible_agent_types",
                parameter_type="set",
            )
        for agent_type in cls.compatible_agent_types:
            if not isinstance(agent_type, BaseAgentType):
                raise ListenerTypeConfigurationParameterTypeError(
                    listener_type_filepath=sys.modules[cls.__module__].__file__,
                    error_message=(
                        "The elements in the set of compatible agent types must be "
                        "agent type objects."
                    ),
                )

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.listener_type_id)})'

    def __repr__(self) -> str:
        return (
            f"ListenerType(name={self.name!r}, "
            f"compatible_agent_types={self.compatible_agent_types!r})"
        )

    def add_compatible_agent_type(self, agent_type: BaseAgentType) -> None:
        if not isinstance(agent_type, BaseAgentType):
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

    def remove_compatible_agent_type(self, agent_type: BaseAgentType) -> None:
        if not isinstance(agent_type, BaseAgentType):
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

    def is_compatible_with_agent_type(self, agent_type: BaseAgentType) -> bool:
        # If `compatible_agent_types` is set to `None`, then the listener is compatible
        # with all agent types.
        if self.compatible_agent_types is None:
            return True
        return agent_type in self.compatible_agent_types

    def get_all_compatible_agent_types(self) -> dict[str, BaseAgentType]:
        return {
            str(agent_type.agent_type_id): agent_type
            for agent_type in self.compatible_agent_types
        }

    def get_compatible_agent_type_by_agent_type_id(
        self,
        agent_type_id: str,
    ) -> BaseAgentType:
        for agent_type in self.compatible_agent_types:
            if str(agent_type.agent_type_id) == agent_type_id:
                return agent_type
        raise AgentTypeNotFoundError

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
