from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException
)
from consortium.server.framework.exceptions.base_framework_exception import (
    BaseFrameworkException as UserRaisedBaseFrameworkException
)


class ListenerFrameworkException(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred in the listeners framework.",
        detail: Any = None,
    ):
        super().__init__(message=message, detail=detail)

    @classmethod
    def create_from_user_raised_framework_exception(cls, exc: UserRaisedBaseFrameworkException):
        cls.__init__(message=exc.message, detail=exc.detail)


class ListenerStartError(ListenerFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while starting the listener.",
        detail: Any = None,
    ):
        super().__init__(message=message, detail=detail)


class ListenerStopError(ListenerFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while stopping the listener.",
        detail: Any = None,
    ):
        super().__init__(message=message, detail=detail)


class ListenerRuntimeError(ListenerFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while the listener was running.",
        detail: Any = None,
    ):
        super().__init__(message=message, detail=detail)
