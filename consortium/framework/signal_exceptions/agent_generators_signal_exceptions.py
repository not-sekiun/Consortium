from consortium.framework.signal_exceptions._component_signal_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)


class AgentGeneratorStartError(ComponentStartError):
    """Raise from a start hook to abort starting the agent generator with an error."""


class AgentGeneratorBuildStepRuntimeError(ComponentRuntimeError):
    """Raise from a build step to signal that an error occurred while building the agent."""


class AgentGeneratorStopError(ComponentStopError):
    """Raise from a stop hook to abort stopping the agent generator with an error."""
