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

# from typing import Any

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
    Raised when an error occurs while attempting to start the listener.
    """

    # def __init__(
    #     self,
    #     message: str = "",
    #     detail: Any = None,
    # ) -> None:
    #     super().__init__(
    #         message=message,
    #         detail=detail,
    #     )


class ListenerRuntimeError(ComponentRuntimeError):
    """
    Raised when an error occurs while the listener is running.
    """

    #
    # def __init__(
    #     self,
    #     message: str = "",
    #     detail: Any = None,
    # ):
    #     super().__init__(
    #         message=message,
    #         detail=detail,
    #     )


class ListenerStopError(ComponentStopError):
    """
    Raised when an error occurs while attempting to stop the listener.
    """

    # def __init__(
    #     self,
    #     message: str = "",
    #     detail: Any = None,
    # ) -> None:
    #     super().__init__(
    #         message=message,
    #         detail=detail,
    #     )


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
