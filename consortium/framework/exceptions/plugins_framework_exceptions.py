from typing import Any

from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


class PluginStartError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the plugin.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class PluginRuntimeError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while the plugin was running.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class PluginStopError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the plugin.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
