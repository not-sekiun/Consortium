from enum import StrEnum


class AgentGeneratorState(StrEnum):
    # Agent build is queued but not yet started, this happens when the agent
    # generator is initialized from the agent template. Afterward, a request must
    # be POSTed to the /api/agent-generator endpoint to start the agent generator
    QUEUED = "QUEUED"
    # Agent build has been started and is currently building the agent. This state
    # is reached after a POST request is sent to the /api/agent-generator endpoint
    BUILDING = "BUILDING"
    # Agent build has finished successfully, at this point the agent is ready to be
    # downloaded
    COMPLETED = "COMPLETED"
    # Agent build has errored
    ERRORED = "ERRORED"
    # Agent build has been manually cancelled by the user via a DELETE request to
    # the relevant /api/agent-generator endpoint
    CANCELLED = "CANCELLED"
    # Agent generator has experienced a fatal error and is no longer running. Any
    # unhandled exceptions will trigger this state
    FATAL = "FATAL"


class AgentGeneratorStatus:
    def __init__(self):
        # AgentGeneratorStatus is instantiated at the point of instantiation of the
        # agent generator. When the agent generator is instantiated it is not
        # automatically running, hence the initial state of QUEUED
        self.state = AgentGeneratorState.QUEUED
        self.exception = None

    def transition_to_queued(self) -> None:
        self.state = AgentGeneratorState.QUEUED
        self.exception = None

    def transition_to_building(self) -> None:
        self.state = AgentGeneratorState.BUILDING
        self.exception = None

    def transition_to_completed(self) -> None:
        self.state = AgentGeneratorState.COMPLETED
        self.exception = None

    def transition_to_errored(
        self,
        exception: Exception,
    ) -> None:
        self.state = AgentGeneratorState.ERRORED
        self.exception = exception

    def transition_to_cancelled(self) -> None:
        self.state = AgentGeneratorState.CANCELLED
        self.exception = None

    def transition_to_fatal(self, exc: Exception) -> None:
        self.state = AgentGeneratorState.FATAL
        self.exception = exc

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


class AgentGeneratorBuildStepStatus: ...
