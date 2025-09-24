import enum

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)
from consortium.server.exceptions.framework_exceptions.lifecycle_exceptions import (
    LifeCycleRuntimeError,
)


class LifeCycleState(enum.StrEnum):
    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class LifeCycleStatus:
    _VALID_LIFE_CYCLE_STATE_TRANSITIONS = {
        LifeCycleState.INITIALIZED: {LifeCycleState.STARTED},
        LifeCycleState.STARTED: {
            LifeCycleState.INITIALIZED,
            LifeCycleState.RUNNING,
            LifeCycleState.FATAL,
        },
        LifeCycleState.RUNNING: {
            LifeCycleState.COMPLETED,
            LifeCycleState.STOPPED,
            LifeCycleState.CANCELLED,
            LifeCycleState.ERRORED,
            LifeCycleState.FATAL,
        },
        LifeCycleState.STOPPED: {
            LifeCycleState.STARTED,
            LifeCycleState.FATAL,
        },
        LifeCycleState.CANCELLED: {
            LifeCycleState.STARTED,
            LifeCycleState.FATAL,
        },
        LifeCycleState.ERRORED: {
            LifeCycleState.STARTED,
            LifeCycleState.FATAL,
        },
        LifeCycleState.FATAL: {
            LifeCycleState.STARTED,
        },
    }

    def __init__(self):
        self.state = LifeCycleState.INITIALIZED
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
        new_state: LifeCycleState,
        error: BaseFrameworkException | None = None,
    ):
        if new_state not in self._VALID_LIFE_CYCLE_STATE_TRANSITIONS[self.state]:
            raise ValueError(
                f"Invalid state transition from current state '{self.state}' to new "
                f"state '{new_state}'.",
            )
        if (
            new_state in (LifeCycleState.ERRORED, LifeCycleState.FATAL)
            and error is None
        ):
            raise ValueError(
                f"When transitioning to the '{new_state}' state, an error must be "
                f"provided.",
            )
        if (
            new_state not in (LifeCycleState.ERRORED, LifeCycleState.FATAL)
            and error is not None
        ):
            raise ValueError(
                f"When transitioning to the '{new_state}' state, no error must be "
                f"provided.",
            )
        self.state = new_state
        self.error = error

    def _transition_to_initialized(self) -> None:
        self._transition_to_state(new_state=LifeCycleState.INITIALIZED)

    def _transition_to_started(self) -> None:
        self._transition_to_state(new_state=LifeCycleState.STARTED)

    def _transition_to_running(self) -> None:
        self._transition_to_state(new_state=LifeCycleState.RUNNING)

    def _transition_to_completed(self) -> None:
        self._transition_to_state(new_state=LifeCycleState.COMPLETED)

    def _transition_to_stopped(self) -> None:
        self._transition_to_state(new_state=LifeCycleState.STOPPED)

    def _transition_to_cancelled(self) -> None:
        self._transition_to_state(new_state=LifeCycleState.CANCELLED)

    def _transition_to_errored(self, error: BaseFrameworkException) -> None:
        self._transition_to_state(
            new_state=LifeCycleState.ERRORED,
            error=error,
        )

    def _transition_to_fatal(self, exception: Exception) -> None:
        self._transition_to_state(
            new_state=LifeCycleState.FATAL,
            error=LifeCycleRuntimeError(
                message=f"{type(exception).__name__}: {exception}",
                detail={
                    "type": type(exception).__name__,
                    "message": str(exception),
                },
            ),
        )
