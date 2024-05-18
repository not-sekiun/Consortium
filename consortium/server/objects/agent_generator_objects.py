from enum import StrEnum

from consortium.server.framework.exceptions.agent_framework_exceptions import (
    AgentGeneratorBuildError,
)


class AgentGeneratorState(StrEnum):
    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class AgentGeneratorStatus:
    def __init__(self):
        # AgentGeneratorStatus is instantiated at the point of instantiation of the
        # agent generator. When the agent generator is instantiated it is not
        # automatically running, hence the initial state of QUEUED
        self.state = AgentGeneratorState.INITIALIZED
        self.exception = None

    def transition_to_initialized(self) -> None:
        self.state = AgentGeneratorState.INITIALIZED
        self.exception = None

    def transition_to_started(self) -> None:
        self.state = AgentGeneratorState.STARTED
        self.exception = None

    def transition_to_building(self) -> None:
        self.state = AgentGeneratorState.RUNNING
        self.exception = None

    def transition_to_completed(self) -> None:
        self.state = AgentGeneratorState.COMPLETED
        self.exception = None

    def transition_to_stopped(self) -> None:
        self.state = AgentGeneratorState.STOPPED
        self.exception = None

    def transition_to_cancelled(self) -> None:
        self.state = AgentGeneratorState.CANCELLED
        self.exception = None

    def transition_to_errored(self, exception: AgentGeneratorBuildError) -> None:
        self.state = AgentGeneratorState.ERRORED
        self.exception = exception

    def transition_to_fatal(self, exception: Exception) -> None:
        self.state = AgentGeneratorState.FATAL
        self.exception = AgentGeneratorBuildError(
            message="A fatal error occurred while the agent generator was building.",
            detail={
                "type": type(exception).__name__,
                "message": str(exception),
            },
        )

    def to_json(self) -> dict[str, str | None]:
        # Internally the identifier "exception" is more representative of what is stored
        # here. In the API we want to expose this as "error" instead to align the naming
        # convention with other parts of the api that use "error" instead of "exception"
        if not self.exception:
            return {"state": str(self.state), "error": None}
        return {
            "state": str(self.state),
            "error": self.exception.to_json(),
        }


class AgentGeneratorBuildStepState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class AgentGeneratorBuildStepStatus:
    def __init__(self):
        self.state = AgentGeneratorBuildStepState.QUEUED
        self.exception = None

    def transition_to_queued(self) -> None:
        self.state = AgentGeneratorBuildStepState.QUEUED
        self.exception = None

    def transition_to_running(self) -> None:
        self.state = AgentGeneratorBuildStepState.RUNNING
        self.exception = None

    def transition_to_completed(self) -> None:
        self.state = AgentGeneratorBuildStepState.COMPLETED
        self.exception = None

    def transition_to_errored(self, exception: AgentGeneratorBuildError) -> None:
        self.state = AgentGeneratorBuildStepState.ERRORED
        self.exception = exception

    def transition_to_fatal(self, exception: Exception) -> None:
        self.state = AgentGeneratorBuildStepState.FATAL
        self.exception = AgentGeneratorBuildError(
            message="A fatal error occurred while the agent generator was building.",
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
