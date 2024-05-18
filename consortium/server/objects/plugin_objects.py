from enum import StrEnum

from consortium.server.framework.exceptions.plugins_framework_exceptions import (
    PluginRuntimeError,
)


class PluginState(StrEnum):
    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class PluginStatus:
    def __init__(self):
        self.state = PluginState.INITIALIZED
        self.exception = None

    def transition_to_initialized(self) -> None:
        self.state = PluginState.INITIALIZED
        self.exception = None

    def transition_to_started(self) -> None:
        self.state = PluginState.STARTED
        self.exception = None

    def transition_to_running(self) -> None:
        self.state = PluginState.RUNNING
        self.exception = None

    def transition_to_stopped(self) -> None:
        self.state = PluginState.STOPPED
        self.exception = None

    def transition_to_cancelled(self) -> None:
        self.state = PluginState.CANCELLED
        self.exception = None

    def transition_to_errored(self, exception: PluginRuntimeError) -> None:
        self.state = PluginState.ERRORED
        self.exception = exception

    def transition_to_fatal(self, exception: Exception) -> None:
        self.state = PluginState.FATAL
        self.exception = PluginRuntimeError(
            message="A fatal error occurred while the plugin was running.",
            detail={
                "type": type(exception).__name__,
                "message": str(exception),
            },
        )

    def to_json(self) -> dict[str, str | None]:
        # Internally the identifier "exception" is more representative of what is stored
        # here. In the API we want to expose this as "error" instead to align the naming
        # convention with other parts of the api that use "error" instead of "exception"
        return {
            "state": str(self.state),
            "error": self.exception.to_json() if self.exception else None,
        }
