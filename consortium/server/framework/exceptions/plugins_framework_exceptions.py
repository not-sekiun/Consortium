from typing import Any

from consortium.server.framework.exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class PluginStartError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the plugin.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="PLUGIN_START_ERROR",
            message=message,
            detail=detail,
        )


class PluginRuntimeError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while the plugin was running.",
        detail: Any = None,
    ):
        super().__init__(
            code="PLUGIN_RUNTIME_ERROR",
            message=message,
            detail=detail,
        )


class PluginStopError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the plugin.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="PLUGIN_STOP_ERROR",
            message=message,
            detail=detail,
        )


class PluginCancellationError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to cancel the plugin.",
        detail: Any = None,
    ):
        super().__init__(
            code="PLUGIN_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )


class PluginLoadingError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to load the plugin.",
        detail: Any = None,
    ):
        super().__init__(
            code="PLUGIN_LOADING_ERROR",
            message=message,
            detail=detail,
        )


class PluginUnloadingError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to unload the plugin.",
        detail: Any = None,
    ):
        super().__init__(
            code="PLUGIN_UNLOADING_ERROR",
            message=message,
            detail=detail,
        )
