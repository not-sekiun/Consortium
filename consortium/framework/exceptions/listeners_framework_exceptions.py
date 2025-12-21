from consortium.framework.exceptions._component_framework_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)


class ListenerStartError(ComponentStartError):
    """
    Raise this exception to signal that an error occurred while attempting to start the
    listener and to abort the start process.
    """


class ListenerRuntimeError(ComponentRuntimeError):
    """
    Raise this exception to signal that an error occurred while the listener was
    running.
    """


class ListenerStopError(ComponentStopError):
    """
    Raise this exception to signal that an error occurred while attempting to stop the
    listener and to abort the stop process.
    """
