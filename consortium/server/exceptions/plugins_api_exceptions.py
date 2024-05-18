# Errors for the api endpoint /api/plugins.
# - HTTPError
#   - NotFoundError
#     - PluginNotFoundError
# - PluginError
#   - PluginStateError
#     - PluginAlreadyRunningError
#     - PluginNotRunningError
#   - PluginOperationError
#     - PluginStartError
#     - PluginStopError
#     - PluginCancellationError
from typing import Any

from consortium.server.exceptions.base_server_exception import BaseServerException


class PluginError(BaseServerException):
    def __init__(
        self,
        status_code: int = 400,
        code: str = "PLUGIN_ERROR",
        message: str = "A plugin error occurred.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class PluginStateError(PluginError):
    def __init__(
        self,
        status_code: int = 409,
        code: str = "PLUGIN_STATE_ERROR",
        message: str = (
            "A plugin error occurred due to a conflict in the plugin's state."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class PluginAlreadyRunningError(PluginStateError):
    def __init__(
        self,
        message: str = (
            "The plugin is already running. Stop it before performing this operation."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=409,
            code="PLUGIN_ALREADY_RUNNING_ERROR",
            message=message,
            detail=detail,
        )


class PluginNotRunningError(BaseServerException):
    def __init__(
        self,
        message: str = (
            "The plugin is not running. Start it before performing this operation."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=409,
            code="PLUGIN_NOT_RUNNING_ERROR",
            message=message,
            detail=detail,
        )


class PluginOperationError(PluginError):
    def __init__(
        self,
        status_code: int = 400,
        code: str = "PLUGIN_OPERATION_ERROR",
        message: str = "A plugin error occurred while it was in operation.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class PluginStartError(PluginOperationError):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the plugin.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="PLUGIN_START_ERROR",
            message=message,
            detail=detail,
        )


class PluginStopError(PluginOperationError):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the plugin.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="PLUGIN_STOP_ERROR",
            message=message,
            detail=detail,
        )


class PluginCancellationError(PluginOperationError):
    def __init__(
        self,
        message: str = "An error occurred while attempting to cancel the plugin.",
        detail: Any = None,
    ):
        super().__init__(
            status_code=400,
            code="PLUGIN_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )
