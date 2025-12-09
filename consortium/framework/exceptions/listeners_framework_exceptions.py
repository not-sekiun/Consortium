"""
This module defines all the exceptions that are either specifically raised by the
listener to communicate to the framework or are caught by the listener to handle
an error condition from the framework. The overall exception hierarchy is as follows:

- [`BaseFrameworkException`]
    - [`BaseRaiseOnlyFrameworkException`]
        - [`ListenerStartError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerStartError]
        - [`ListenerRuntimeError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerRuntimeError]
        - [`ListenerStopError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerStopError]
    - [`BaseCatchOnlyFrameworkException`]
        - [`ListenerSpecificAgentNotFoundError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerSpecificAgentNotFoundError]
"""

from consortium.framework.exceptions._component_framework_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)
from consortium.framework.exceptions.base_framework_exception import (  # BaseRaiseOnlyFrameworkException,
    BaseCatchOnlyFrameworkException,
)


class ListenerStartError(ComponentStartError):
    """
    Raise this exception to signal that an error occurred while attempting to start the
    listener and to abort the start process.
    """


class ListenerRuntimeError(ComponentRuntimeError):
    """
    Raise this exception to signal that an error occurred while the listener was
    running.
    """


class ListenerStopError(ComponentStopError):
    """
    Raise this exception to signal that an error occurred while attempting to stop the
    listener and to abort the stop process.
    """


# TODO: Maybe use the standard AgentNotFoundError from the service instead of creating
#  a new one?
class ListenerSpecificAgentNotFoundError(BaseCatchOnlyFrameworkException):
    """
    Raised when the requested agent is not found with the provided agent ID when
    attempting a specific operation with the particular
    [agents manager object][consortium.server.objects.listener_objects.AgentsManager]
    that is specific to a [listener object][consortium.framework.base_listener.BaseListener].
    """

    def __init__(
        self,
        agent_id: str,
    ) -> None:
        super().__init__(
            message=(
                f"Failed to find the requested agent. No agent was found with the "
                f"provided agent ID '{agent_id}'."
            ),
        )
