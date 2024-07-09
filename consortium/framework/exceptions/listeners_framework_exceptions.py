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
    BaseFrameworkException,
)


class ListenerStartError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the listener.",
        detail: Any = None,
    ) -> None:
        self.code = "LISTENER_START_ERROR"
        super().__init__(
            message=message,
            detail=detail,
        )


class ListenerRuntimeError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while the listener was running.",
        detail: Any = None,
    ):
        self.code = "LISTENER_RUNTIME_ERROR"
        super().__init__(
            message=message,
            detail=detail,
        )


class ListenerStopError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the listener.",
        detail: Any = None,
    ) -> None:
        self.code = "LISTENER_STOP_ERROR"
        super().__init__(
            message=message,
            detail=detail,
        )
