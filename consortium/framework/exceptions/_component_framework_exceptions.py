from typing import Any

from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


class ComponentStartError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = "",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class ComponentRuntimeError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = "",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class ComponentStopError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = "",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
