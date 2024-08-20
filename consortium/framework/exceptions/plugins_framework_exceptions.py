from typing import Any

from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


class PluginStartError(BaseRaiseOnlyFrameworkException):
    code = "PLUGIN_START_ERROR"

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
    code = "PLUGIN_RUNTIME_ERROR"

    def __init__(
        self,
        message: str = "An error occurred while the plugin was running.",
        detail: Any = None,
    ):
        super().__init__(
            message=message,
            detail=detail,
        )


class PluginStopError(BaseRaiseOnlyFrameworkException):
    code = "PLUGIN_STOP_ERROR"

    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the plugin.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
