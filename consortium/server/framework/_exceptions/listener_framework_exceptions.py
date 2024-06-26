from typing import Any

from consortium.server.framework._exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ListenerStartError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="LISTENER_START_ERROR",
            message=message,
            detail=detail,
        )


class ListenerRuntimeError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while the listener was running.",
        detail: Any = None,
    ):
        super().__init__(
            code="LISTENER_RUNTIME_ERROR",
            message=message,
            detail=detail,
        )


class ListenerStopError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="LISTENER_STOP_ERROR",
            message=message,
            detail=detail,
        )


class ListenerCancellationError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to cancel the listener.",
        detail: Any = None,
    ):
        super().__init__(
            code="LISTENER_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )
