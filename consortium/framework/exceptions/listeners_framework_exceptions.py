"""
- BaseFrameworkException: Base class for all framework related exceptions.
  - ListenerStartError: Raised when an error occurs while attempting to start the
  listener.
  - ListenerRuntimeError: Raised when an error occurs while the listener is running.
  - ListenerStopError: Raised when an error occurs while attempting to stop the
  listener.
"""

from typing import Any

from consortium.framework.exceptions.base_framework_exception import (
    BaseCatchOnlyFrameworkException,
    BaseRaiseOnlyFrameworkException,
)


class ListenerStartError(BaseRaiseOnlyFrameworkException):
    code = "LISTENER_START_ERROR"

    def __init__(
        self,
        message: str = "An error occurred while attempting to start the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class ListenerRuntimeError(BaseRaiseOnlyFrameworkException):
    code = "LISTENER_RUNTIME_ERROR"

    def __init__(
        self,
        message: str = "An error occurred while the listener was running.",
        detail: Any = None,
    ):
        super().__init__(
            message=message,
            detail=detail,
        )


class ListenerStopError(BaseRaiseOnlyFrameworkException):
    code = "LISTENER_STOP_ERROR"

    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class ListenerSpecificAgentNotFoundError(BaseCatchOnlyFrameworkException):
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
