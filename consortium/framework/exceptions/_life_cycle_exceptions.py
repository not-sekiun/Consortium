from typing import Any

from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


class LifeCycleStartError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str,
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class LifeCycleRuntimeError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str,
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class LifeCycleStopError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str,
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
