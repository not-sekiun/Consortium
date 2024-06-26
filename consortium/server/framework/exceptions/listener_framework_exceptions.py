"""
- BaseFrameworkException: Base class for all framework related exceptions.
  - ListenerConfigurationError: Raised when an error occurs in the configuration of the
  listener.
  - ListenerStartError: Raised when an error occurs while attempting to start the
  listener.
  - ListenerRuntimeError: Raised when an error occurs while the listener is running.
  - ListenerStopError: Raised when an error occurs while attempting to stop the
  listener.
"""

from typing import Any

from consortium.server.framework.exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ListenerConfigurationError(BaseFrameworkException):
    def __init__(self, error_message: str):
        super().__init__(
            f"Error in the configuration of the listener: {error_message}",
        )


class ListenerStartError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the listener.",
        detail: Any = None,
    ) -> None:
        self.code = "LISTENER_START_ERROR"
        self.message = message
        self.detail = detail
        super().__init__(
            message=message,
        )


class ListenerRuntimeError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while the listener was running.",
        detail: Any = None,
    ):
        self.code = ("LISTENER_RUNTIME_ERROR",)
        self.message = (message,)
        self.detail = (detail,)
        super().__init__(
            message=message,
        )


class ListenerStopError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the listener.",
        detail: Any = None,
    ) -> None:
        self.code = ("LISTENER_STOP_ERROR",)
        self.message = (message,)
        self.detail = (detail,)
        super().__init__(
            message=message,
        )
