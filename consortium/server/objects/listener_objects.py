from enum import StrEnum

from consortium.server.exceptions.framework_exceptions.listeners_framework_exceptions import (
    ListenerRuntimeError,
)


class ListenerState(StrEnum):
    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class ListenerStatus:
    def __init__(self):
        self.state = ListenerState.INITIALIZED
        self.exception = None

    def transition_to_initialized(self) -> None:
        self.state = ListenerState.INITIALIZED
        self.exception = None

    def transition_to_started(self) -> None:
        self.state = ListenerState.STARTED
        self.exception = None

    def transition_to_running(self) -> None:
        self.state = ListenerState.RUNNING
        self.exception = None

    def transition_to_stopped(self) -> None:
        self.state = ListenerState.STOPPED
        self.exception = None

    def transition_to_cancelled(self) -> None:
        self.state = ListenerState.CANCELLED
        self.exception = None

    def transition_to_errored(self, exception: ListenerRuntimeError) -> None:
        self.state = ListenerState.ERRORED
        self.exception = exception

    def transition_to_fatal(self, exception: Exception) -> None:
        self.state = ListenerState.FATAL
        self.exception = ListenerRuntimeError(
            message="A fatal error occurred while the listener was running.",
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
