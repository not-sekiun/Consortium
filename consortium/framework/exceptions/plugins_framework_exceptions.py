from typing import Any

from consortium.framework.exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class PluginStartError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the plugin.",
        detail: Any = None,
    ) -> None:
        self.code = "PLUGIN_START_ERROR"
        super().__init__(
            message=message,
            detail=detail,
        )


class PluginRuntimeError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while the plugin was running.",
        detail: Any = None,
    ):
        self.code = "PLUGIN_RUNTIME_ERROR"
        super().__init__(
            message=message,
            detail=detail,
        )


class PluginStopError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the plugin.",
        detail: Any = None,
    ) -> None:
        self.code = "PLUGIN_STOP_ERROR"
        super().__init__(
            message=message,
            detail=detail,
        )
