from enum import StrEnum

from consortium.server.exceptions.framework_exceptions.agent_generators_framework_exceptions import (
    AgentGeneratorBuildError,
    AgentGeneratorBuildStepError,
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

    def transition_to_fatal(
        self,
        agent_generator_str: str,
        exception: Exception,
    ) -> None:
        self.state = AgentGeneratorState.FATAL
        self.exception = AgentGeneratorBuildError(
            agent_generator_str=agent_generator_str,
            error_message=f"{type(exception).__name__}: {exception}",
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
        # TODO: Fix this temporary hack by formalizing the return structure of
        #  framework exceptions???
        error_dict = self.exception.to_json()
        error_dict["code"] = "AGENT_GENERATOR_BUILD_ERROR"
        return {
            "state": str(self.state),
            "error": error_dict,
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

    def transition_to_fatal(
        self,
        agent_generator_build_step_identifier: str,
        exception: Exception,
    ) -> None:
        self.state = AgentGeneratorBuildStepState.FATAL
        self.exception = AgentGeneratorBuildStepError(
            agent_generator_build_step_str=agent_generator_build_step_identifier,
            error_message=f"{type(exception).__name__}: {exception}",
            detail={
                "type": type(exception).__name__,
                "message": str(exception),
            },
        )

    def to_json(self) -> dict[str, str | None]:
        # Internally the identifier "exception" is more representative of what is stored
        # here. In the API we want to expose this as "error" instead to align the naming
        # convention with other parts of the api that use "error" instead of "exception"
        # TODO: Fix this temporary hack by formalizing the return structure of
        #  framework exceptions???
        if not self.exception:
            return {
                "state": str(self.state),
                "error": None,
            }
        error_dict = self.exception.to_json()
        error_dict["code"] = "AGENT_GENERATOR_BUILD_STEP_ERROR"
        return {
            "state": str(self.state),
            "error": error_dict,
        }
