from consortium.framework.exceptions._component_framework_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)


class AgentGeneratorStartError(ComponentStartError):
    """
    Raise this exception to signal that an error occurred while attempting to start the
    agent generator to abort the start process.
    """


class AgentGeneratorBuildStepRuntimeError(ComponentRuntimeError):
    """
    Raise this exception to signal that an error occurred while the agent generator was
    building the agent.
    """


class AgentGeneratorStopError(ComponentStopError):
    """
    Raise this exception to signal that an error occurred while attempting to stop the
    agent generator and to abort the stop process.
    """
