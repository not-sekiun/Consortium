from consortium.framework.signal_exceptions._component_signal_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)


class ListenerStartError(ComponentStartError):
    """Raise from a start hook to abort starting the listener with an error."""


class ListenerRuntimeError(ComponentRuntimeError):
    """Raise from a runtime hook to signal that an error occurred while the listener ran."""


class ListenerStopError(ComponentStopError):
    """Raise from a stop hook to abort stopping the listener with an error."""
