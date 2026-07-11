import enum

from consortium.server.exceptions.consortium_exceptions.components_consortium_exceptions import (
    ComponentRuntimeError,
)


class State(enum.StrEnum):
    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class Status:
    _VALID_STATE_TRANSITIONS = {
        # `reset()` can be called on an INITIALIZED component to re-initialize it.
        # `reset()` should be idempotent so we allow transitioning from INITIALIZED to
        # INITIALIZED.
        State.INITIALIZED: {State.INITIALIZED, State.STARTED},
        State.STARTED: {
            State.INITIALIZED,
            State.RUNNING,
            State.FATAL,
        },
        State.RUNNING: {
            State.COMPLETED,
            State.STOPPING,
            State.STOPPED,
            State.CANCELLED,
            State.ERRORED,
            State.FATAL,
        },
        State.COMPLETED: {
            State.INITIALIZED,
            State.STARTED,
            State.FATAL,
        },
        State.STOPPING: {
            State.STOPPED,
            State.FATAL,
        },
        State.STOPPED: {
            State.INITIALIZED,
            State.STARTED,
            State.FATAL,
        },
        State.CANCELLED: {
            State.INITIALIZED,
            State.STARTED,
            State.FATAL,
        },
        State.ERRORED: {
            State.INITIALIZED,
            State.STARTED,
            State.FATAL,
        },
        State.FATAL: {
            State.INITIALIZED,
            State.STARTED,
        },
    }

    def __init__(self):
        self.state = State.INITIALIZED
        self.error = None

    def __str__(self) -> str:
        return f"{self.state}: {self.error}" if self.error is not None else self.state

    def __repr__(self) -> str:
        return f"Status(state={self.state!r}, error={self.error!r})"

    def to_json(self):
        return {
            "state": str(self.state),
            "error": {
                "code": self.error.code,
                "message": self.error.message,
                "detail": self.error.detail,
            }
            if isinstance(self.error, ComponentRuntimeError)
            else None,
        }

    def _transition_to_state(
        self,
        new_state: State,
        error: ComponentRuntimeError | None = None,
    ):
        if new_state not in self._VALID_STATE_TRANSITIONS[self.state]:
            raise AssertionError(
                f"Invalid status transition from current status '{self.state}' to new "
                f"status '{new_state}'.",
            )
        if new_state in (State.ERRORED, State.FATAL) and error is None:
            raise AssertionError(
                f"When transitioning to the '{new_state}' status, an error must be "
                f"provided.",
            )
        if new_state not in (State.ERRORED, State.FATAL) and error is not None:
            raise AssertionError(
                f"When transitioning to the '{new_state}' status, no error should be "
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

    def _transition_to_stopping(self) -> None:
        self._transition_to_state(new_state=State.STOPPING)

    def _transition_to_stopped(self) -> None:
        self._transition_to_state(new_state=State.STOPPED)

    def _transition_to_cancelled(self) -> None:
        self._transition_to_state(new_state=State.CANCELLED)

    def _transition_to_errored(self, error: ComponentRuntimeError) -> None:
        self._transition_to_state(new_state=State.ERRORED, error=error)

    def _transition_to_fatal(self, error: ComponentRuntimeError) -> None:
        self._transition_to_state(new_state=State.FATAL, error=error)
