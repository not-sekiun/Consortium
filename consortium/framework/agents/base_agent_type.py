import sys
from typing import get_type_hints

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

from consortium.framework._core.framework_exceptions.c2_types_framework_exceptions import (
    AgentTypeConfigurationParameterTypeError,
    EmptyAgentTypeNameError,
)
from consortium.framework.agents.base_agent_capability import BaseAgentCapability


class _BaseAgentTypeModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    name: str
    agent_capabilities: set[type[BaseAgentCapability]]


class BaseAgentType:
    """Defines the set of capabilities available to a specific category of agent.

    An agent type groups related BaseAgentCapability classes under a shared name,
    allowing the framework to route incoming task commands to the correct capability
    implementation. Declare agent_capabilities at the class level; the framework
    converts the set into a name-keyed dictionary at class definition time for fast
    lookup during task dispatch.

    Attributes:
        name (str): Unique identifier for this agent type. Required and must be non-empty.
        agent_capabilities (set[type[BaseAgentCapability]] | None): The capability
            classes this agent type exposes. Converted to a name-keyed dict at class
            definition time.
    """

    name: str
    agent_capabilities: set[type[BaseAgentCapability]] | None = None

    def __init_subclass__(cls, **kwargs):
        cls.agent_capabilities = cls.agent_capabilities or set()

        try:
            _BaseAgentTypeModel(
                name=cls.name,
                agent_capabilities=cls.agent_capabilities,
            )
        except ValidationError as exc:
            raise AgentTypeConfigurationParameterTypeError(
                agent_type_filepath=sys.modules[cls.__module__].__file__,
                parameter_name=str(exc.errors()[0]["loc"][0]),
                parameter_type=get_type_hints(_BaseAgentTypeModel)[
                    exc.errors()[0]["loc"][0]
                ],
            ) from None

        if not cls.name:
            raise EmptyAgentTypeNameError(
                agent_type_filepath=sys.modules[cls.__module__].__file__,
            )

        # Reassign agent_capabilities to be a dictionary mapping capability names to
        # capability types for easier usage.
        cls.agent_capabilities = {
            agent_capability.name: agent_capability
            for agent_capability in cls.agent_capabilities
        }

    def __str__(self) -> str:
        return f"'{self.name}'"

    def __repr__(self) -> str:
        return (
            f"AgentType("
            f"name={self.name!r}, "
            f"agent_capabilities={self.agent_capabilities!r}"
            f")"
        )

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the agent type and its capabilities to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the agent type name and a nested mapping of each
            capability name to its serialized JSON representation.
        """
        return {
            "name": self.name,
            "agent_capabilities": {
                name: agent_capability.to_json()
                for name, agent_capability in self.agent_capabilities.items()
            },
        }
