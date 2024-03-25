from enum import StrEnum

from consortium.server.framework.framework_exceptions import (
    ListenerCancellationError,
    ListenerRuntimeError,
    ListenerStartError,
    ListenerStopError,
)


class ListenerState(StrEnum):
    # Listener has been started but is not yet running, preliminary checks are being
    # performed
    STARTED = "STARTED"
    # Listener is currently running in the main loop
    RUNNING = "RUNNING"
    # Listener has been stopped and is no longer running
    STOPPED = "STOPPED"
    # Listener has been cancelled, this is a form of force stopping the listener
    CANCELLED = "CANCELLED"
    # Listener has failed, the failure can be due to a number of reasons, such as a
    # failed startup validation. Exceptions at runtime can trigger this state as
    # well
    ERRORED = "ERRORED"
    # Listener has experienced a fatal error and is no longer running. Any unhandled
    # exceptions will trigger this state
    FATAL = "FATAL"


class ListenerStatus:
    def __init__(self):
        # ListenerStatus is instantiated at the point of instantiation of the listener.
        # When the listener is instantiated it is not automatically running, hence the
        # initial state of STOPPED
        self.state = ListenerState.STOPPED
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

    def transition_to_errored(
        self,
        exception: (
            ListenerStartError
            | ListenerRuntimeError
            | ListenerStopError
            | ListenerCancellationError
        ),
    ) -> None:
        self.state = ListenerState.ERRORED
        self.exception = exception

    def transition_to_fatal(self, exception: Exception) -> None:
        self.state = ListenerState.FATAL
        self.exception = exception

    def to_json(self) -> dict[str, str | None]:
        # internally the identifier "exception" is more representative of what is stored
        # here. In the API we want to expose this as "error" instead to align the naming
        # convention with other parts of the api that use "error" instead of "exception"
        if not self.exception:
            return {"state": str(self.state), "error": None}
        return {
            "state": str(self.state),
            "error": self.exception.to_json(),
        }
