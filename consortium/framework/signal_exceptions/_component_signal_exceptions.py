from pydantic import JsonValue

from consortium.framework.signal_exceptions.base_signal_exception import (
    BaseSignalException,
)


class ComponentStartError(BaseSignalException):
    def __init__(
        self,
        message: str = "",
        detail: dict[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class ComponentRuntimeError(BaseSignalException):
    def __init__(
        self,
        message: str = "",
        detail: dict[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class ComponentStopError(BaseSignalException):
    def __init__(
        self,
        message: str = "",
        detail: dict[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
