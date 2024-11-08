import sys
import uuid

from consortium.server.exceptions.framework_exceptions.c2_types_framework_exceptions import (
    AgentTypeAlreadyExistsError,
    AgentTypeNotFoundError,
    EmptyListenerTypeNameError,
    ListenerTypeConfigurationParameterTypeError,
)


class BaseListenerType:
    name: str
    compatible_agent_types: set["BaseAgentType"] | None = None

    def __init__(self):
        self.listener_type_id = uuid.uuid4()

    def __init_subclass__(cls, **kwargs):
        # FIXME: Importing here to avoid circular imports.
        from consortium.framework.agents.base_agent_type import BaseAgentType

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

        # These agent types are the ones that were included in the compatible
        # agent types set in the subclassing class attribute definition. However,
        # these agent types are not yet aware of the listener type. We need to add the
        # listener type to the compatible listener types set of each agent type.
        for agent_type in cls.compatible_agent_types:
            agent_type.add_compatible_listener_type(listener_type=cls())

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.listener_type_id)})"

    def __repr__(self) -> str:
        return (
            f"ListenerType(name={self.name!r}, "
            f"compatible_agent_types={self.compatible_agent_types!r})"
        )

    def add_compatible_agent_type(self, agent_type: "BaseAgentType") -> None:
        # FIXME: Importing here to avoid circular imports.
        from consortium.framework.agents.base_agent_type import BaseAgentType

        if not isinstance(agent_type, BaseAgentType):
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[self.__class__.__module__].__file__,
                error_message=(
                    f"Invalid agent type '{agent_type}' provided, expected an agent "
                    "type object."
                ),
            )
        if agent_type in self.compatible_agent_types:
            raise AgentTypeAlreadyExistsError(
                agent_type=agent_type,
                listener_type=self,
            )
        self.compatible_agent_types.add(agent_type)
        agent_type.compatible_listener_types.add(self)

    def remove_compatible_agent_type(self, agent_type: "BaseAgentType") -> None:
        # FIXME: Importing here to avoid circular imports.
        from consortium.framework.agents.base_agent_type import BaseAgentType

        if not isinstance(agent_type, BaseAgentType):
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[self.__class__.__module__].__file__,
                error_message=(
                    f"Invalid agent type '{agent_type}' provided, expected an agent "
                    "type object."
                ),
            )
        if agent_type not in self.compatible_agent_types:
            raise AgentTypeNotFoundError(
                agent_type=agent_type,
                listener_type=self,
            )
        self.compatible_agent_types.remove(agent_type)
        agent_type.compatible_listener_types.remove(self)

    def is_compatible_with_agent_type(self, agent_type: "BaseAgentType") -> bool:
        # If `compatible_agent_types` is set to `None`, then the listener is compatible
        # with all agent types.
        if self.compatible_agent_types is None:
            return True
        return agent_type in self.compatible_agent_types

    def get_all_compatible_agent_types(self) -> dict[str, "BaseAgentType"]:
        return {
            str(agent_type.agent_type_id): agent_type
            for agent_type in self.compatible_agent_types
        }

    def get_compatible_agent_type_by_agent_type_id(
        self,
        agent_type_id: str,
    ) -> "BaseAgentType":
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
