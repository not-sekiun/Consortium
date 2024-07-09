"""
Exception hierarchy for C2 types framework:

- BaseFrameworkException: Base class for all framework exceptions.
  - ListenerTypeConfigurationError: Error in the configuration of the listener type.
  - ListenerTypeAlreadyExistsError: Listener type already exists in the set of
  compatible listener types for the specified agent type.
  - ListenerTypeNotFoundError: Listener type not found in the set of compatible
  listener types for the specified agent type.
  - AgentTypeConfigurationError: Error in the configuration of the agent type.
  - AgentTypeAlreadyExistsError: Agent type already exists in the set of compatible
  agent types for the specified listener type.
  - AgentTypeNotFoundError: Agent type not found in the set of compatible agent types
  for the specified listener type.
"""

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ListenerTypeConfigurationError(BaseFrameworkException):
    def __init__(self, error_message: str):
        super().__init__(
            f"Error in the configuration of the listener type: {error_message}",
        )


class ListenerTypeAlreadyExistsError(BaseFrameworkException):
    # Use the `ListenerType` and `AgentType` class names as strings in the type hints
    # to avoid circular import issues.
    def __init__(self, listener_type: "ListenerType", agent_type: "AgentType"):
        super().__init__(
            f"Listener type '{listener_type}' already exists in the set of compatible "
            f"listener types for agent type: {agent_type}",
        )


class ListenerTypeNotFoundError(BaseFrameworkException):
    def __init__(self, listener_type: "ListenerType", agent_type: "AgentType"):
        super().__init__(
            f"Listener type '{listener_type}' not found in the set of compatible "
            f"listener types for agent type: {agent_type}",
        )


class AgentTypeConfigurationError(BaseFrameworkException):
    def __init__(self, error_message: str):
        super().__init__(
            f"Error in the configuration of the agent type: {error_message}",
        )


class AgentTypeAlreadyExistsError(BaseFrameworkException):
    def __init__(self, agent_type: "AgentType", listener_type: "ListenerType"):
        super().__init__(
            f"Agent type '{agent_type}' already exists in the set of compatible agent "
            f"types for listener type: {listener_type}",
        )


class AgentTypeNotFoundError(BaseFrameworkException):
    def __init__(self, agent_type: "AgentType", listener_type: "ListenerType"):
        super().__init__(
            f"Agent type '{agent_type}' not found in the set of compatible agent "
            f"types for listener type: {listener_type}",
        )
