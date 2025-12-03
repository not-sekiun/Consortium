import enum

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)
from consortium.server.exceptions.framework_exceptions.components_framework_exceptions import (
    ComponentRuntimeError,
)


class ComponentState(enum.StrEnum):
    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class ComponentStatus:
    _VALID_LIFE_CYCLE_STATE_TRANSITIONS = {
        ComponentState.INITIALIZED: {ComponentState.STARTED},
        ComponentState.STARTED: {
            ComponentState.INITIALIZED,
            ComponentState.RUNNING,
            ComponentState.FATAL,
        },
        ComponentState.RUNNING: {
            ComponentState.COMPLETED,
            ComponentState.STOPPED,
            ComponentState.CANCELLED,
            ComponentState.ERRORED,
            ComponentState.FATAL,
        },
        ComponentState.STOPPED: {
            ComponentState.STARTED,
            ComponentState.FATAL,
        },
        ComponentState.CANCELLED: {
            ComponentState.STARTED,
            ComponentState.FATAL,
        },
        ComponentState.ERRORED: {
            ComponentState.STARTED,
            ComponentState.FATAL,
        },
        ComponentState.FATAL: {
            ComponentState.STARTED,
        },
    }

    def __init__(self):
        self.state = ComponentState.INITIALIZED
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
        new_state: ComponentState,
        error: BaseFrameworkException | None = None,
    ):
        if new_state not in self._VALID_LIFE_CYCLE_STATE_TRANSITIONS[self.state]:
            raise ValueError(
                f"Invalid state transition from current state '{self.state}' to new "
                f"state '{new_state}'.",
            )
        if (
            new_state in (ComponentState.ERRORED, ComponentState.FATAL)
            and error is None
        ):
            raise ValueError(
                f"When transitioning to the '{new_state}' state, an error must be "
                f"provided.",
            )
        if (
            new_state not in (ComponentState.ERRORED, ComponentState.FATAL)
            and error is not None
        ):
            raise ValueError(
                f"When transitioning to the '{new_state}' state, no error must be "
                f"provided.",
            )
        self.state = new_state
        self.error = error

    def _transition_to_initialized(self) -> None:
        self._transition_to_state(new_state=ComponentState.INITIALIZED)

    def _transition_to_started(self) -> None:
        self._transition_to_state(new_state=ComponentState.STARTED)

    def _transition_to_running(self) -> None:
        self._transition_to_state(new_state=ComponentState.RUNNING)

    def _transition_to_completed(self) -> None:
        self._transition_to_state(new_state=ComponentState.COMPLETED)

    def _transition_to_stopped(self) -> None:
        self._transition_to_state(new_state=ComponentState.STOPPED)

    def _transition_to_cancelled(self) -> None:
        self._transition_to_state(new_state=ComponentState.CANCELLED)

    def _transition_to_errored(self, error: BaseFrameworkException) -> None:
        self._transition_to_state(
            new_state=ComponentState.ERRORED,
            error=error,
        )

    def _transition_to_fatal(self, exception: Exception) -> None:
        self._transition_to_state(
            new_state=ComponentState.FATAL,
            error=ComponentRuntimeError(
                message=f"{type(exception).__name__}: {exception}",
                detail={
                    "type": type(exception).__name__,
                    "message": str(exception),
                },
            ),
        )
