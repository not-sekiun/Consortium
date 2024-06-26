"""
- BaseFrameworkException: Base class for all framework related exceptions.
  - ListenerTypeConfigurationError: Raised when an error occurs while configuring a
  listener type.
  - ListenerTypeAlreadyExistsError: Raised when a listener type already exists when a
  new listener type is attempted to be added to the set of compatible listener types
  for an agent type.
  - ListenerTypeNotFoundError: Raised when a listener type is not found when attempting
  to remove a listener type from the set of compatible listener types of an agent type.
  - AgentTypeConfigurationError: Raised when an error occurs while configuring an agent
  type.
  - AgentTypeAlreadyExistsError: Raised when an agent type already exists when a new
  agent type is attempted to be added to the set of compatible agent types for a
  listener type.
  - AgentTypeNotFoundError: Raised when an agent type is not found when attempting to
  remove an agent type from the set of compatible agent types of a listener type.
"""

from consortium.server.framework.exceptions.base_framework_exception import (
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
