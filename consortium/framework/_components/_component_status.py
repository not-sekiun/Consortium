import enum

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class State(enum.StrEnum):
    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class Status:
    _VALID_STATE_TRANSITIONS = {
        State.INITIALIZED: {State.STARTED},
        State.STARTED: {
            State.INITIALIZED,
            State.RUNNING,
            State.FATAL,
        },
        State.RUNNING: {
            State.COMPLETED,
            State.STOPPED,
            State.CANCELLED,
            State.ERRORED,
            State.FATAL,
        },
        State.STOPPED: {
            State.STARTED,
            State.FATAL,
        },
        State.CANCELLED: {
            State.STARTED,
            State.FATAL,
        },
        State.ERRORED: {
            State.STARTED,
            State.FATAL,
        },
        State.FATAL: {
            State.STARTED,
        },
    }

    def __init__(self):
        self.state = State.INITIALIZED
        self.error = None

    def to_json(self):
        return {
            "state": self.state,
            "error": self.error.to_json()
            if isinstance(self.error, BaseFrameworkException)
            else None,
        }

    def _transition_to_state(
        self,
        new_state: State,
        error: BaseFrameworkException | None = None,
    ):
        if new_state not in self._VALID_STATE_TRANSITIONS[self.state]:
            assert False, (
                f"Invalid state transition from current state '{self.state}' to new "
                f"state '{new_state}'.",
            )
        if new_state in (State.ERRORED, State.FATAL) and error is None:
            assert False, (
                f"When transitioning to the '{new_state}' state, an error must be "
                f"provided.",
            )
        if new_state not in (State.ERRORED, State.FATAL) and error is not None:
            assert False, (
                f"When transitioning to the '{new_state}' state, no error should be "
                f"provided.",
            )
        self.state = new_state
        self.error = error

    def _transition_to_initialized(self) -> None:
        self._transition_to_state(new_state=State.INITIALIZED)

    def _transition_to_started(self) -> None:
        self._transition_to_state(new_state=State.STARTED)

    def _transition_to_running(self) -> None:
        self._transition_to_state(new_state=State.RUNNING)

    def _transition_to_completed(self) -> None:
        self._transition_to_state(new_state=State.COMPLETED)

    def _transition_to_stopped(self) -> None:
        self._transition_to_state(new_state=State.STOPPED)

    def _transition_to_cancelled(self) -> None:
        self._transition_to_state(new_state=State.CANCELLED)

    def _transition_to_errored(self, error: BaseFrameworkException) -> None:
        self._transition_to_state(new_state=State.ERRORED, error=error)

    def _transition_to_fatal(self, error: BaseFrameworkException) -> None:
        self._transition_to_state(new_state=State.FATAL, error=error)
