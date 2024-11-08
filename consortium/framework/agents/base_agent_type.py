import sys
import uuid
from typing import Type

from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.server.exceptions.framework_exceptions.c2_types_framework_exceptions import (
    AgentTypeConfigurationError,
    AgentTypeConfigurationParameterTypeError,
    EmptyAgentTypeNameError,
    ListenerTypeAlreadyExistsError,
    ListenerTypeNotFoundError,
)


class BaseAgentType:
    name: str
    compatible_listener_types: set["BaseListenerType"] | None = None
    agent_capabilities: set[Type[BaseAgentCapability]] | None = None

    def __init__(self):
        self.agent_type_id = uuid.uuid4()

    def __init_subclass__(cls, **kwargs):
        # FIXME: Importing here to avoid circular imports.
        from consortium.framework.listeners.base_listener_type import BaseListenerType

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
            if not issubclass(agent_capability, BaseAgentCapability):
                raise AgentTypeConfigurationParameterTypeError(
                    agent_type_filepath=sys.modules[cls.__module__].__file__,
                    error_message=(
                        "The elements in the set of agent capabilities must be "
                        "agent capability classes."
                    ),
                )

        # These listener types are the ones that were included in the compatible
        # listener types set in the subclassing class attribute definition. However,
        # these listener types are not yet aware of the agent type. We need to add the
        # agent type to the compatible agent types set of each listener type.
        for listener_type in cls.compatible_listener_types:
            listener_type.add_compatible_agent_type(agent_type=cls())

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.agent_type_id)})"

    def __repr__(self) -> str:
        return (
            f"AgentType(name={self.name!r}, "
            f"compatible_listener_types={self.compatible_listener_types!r})"
        )

    def add_compatible_listener_type(self, listener_type: "BaseListenerType") -> None:
        # FIXME: Importing here to avoid circular imports.
        from consortium.framework.listeners.base_listener_type import BaseListenerType

        if not isinstance(listener_type, BaseListenerType):
            raise AgentTypeConfigurationParameterTypeError(
                agent_type_filepath=sys.modules[self.__class__.__module__].__file__,
                error_message=(
                    f"Invalid listener type '{listener_type}' provided, expected a "
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
        # FIXME: Importing here to avoid circular imports.
        from consortium.framework.listeners.base_listener_type import BaseListenerType

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
