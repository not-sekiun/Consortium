from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    ComponentAlreadyRunningError,
    ComponentFatalError,
    ComponentNotRunningError,
    ComponentOperationError,
    ComponentRuntimeError,
    ComponentsFrameworkError,
    ComponentStartError,
    ComponentStateError,
    ComponentStopError,
)


class ListenersFrameworkError(
    ComponentsFrameworkError,
):
    """Base exception for all errors that occur within the listeners framework."""

    code = "LISTENERS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "listener"


class ListenerOperationError(
    ComponentOperationError,
    ListenersFrameworkError,
):
    """Base exception for all errors that occur during the operation of a particular
    listener.
    """

    code = "LISTENER_OPERATION_ERROR"


class ListenerStartError(ComponentStartError, ListenerOperationError):
    """Raised when a listener fails to start during listener operation."""

    code = "LISTENER_START_ERROR"


class ListenerRuntimeError(ComponentRuntimeError, ListenerOperationError):
    """Raised when a listener encounters an unhandled error at runtime during listener
    operation.
    """

    code = "LISTENER_RUNTIME_ERROR"


class ListenerStopError(ComponentStopError, ListenerOperationError):
    """Raised when a listener fails to stop during listener operation."""

    code = "LISTENER_STOP_ERROR"


class ListenerFatalError(ComponentFatalError, ListenerOperationError):
    """Raised when an unhandled exception escapes one of a listener's life cycle hooks,
    terminating the listener fatally during listener operation.
    """

    code = "LISTENER_FATAL_ERROR"


class ListenerStateError(
    ComponentStateError,
    ListenersFrameworkError,
):
    """Base exception for all errors that occur due to invalid listener status during
    listener operation.
    """

    code = "LISTENER_STATE_ERROR"


class ListenerNotRunningError(
    ComponentNotRunningError,
    ListenerStateError,
):
    """Raised when an operation is attempted on a listener that requires the listener to
    already be running but the listener is not running.
    """

    code = "LISTENER_NOT_RUNNING_ERROR"


class ListenerAlreadyRunningError(
    ComponentAlreadyRunningError,
    ListenerStateError,
):
    """Raised when an operation is attempted on a listener that requires the listener to
    not already be started or running but the listener is already started or running.
    """

    code = "LISTENER_ALREADY_RUNNING_ERROR"


class ListenerCreationError(ListenersFrameworkError):
    """Base exception for all errors that occur during the creation of a listener."""

    code = "LISTENER_CREATION_ERROR"


class ListenerCreationParameterTypeError(ListenerCreationError):
    """Raised when a provided listener parameter is not of the expected type during
    listener creation.
    """

    code = "LISTENER_CREATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        listener_str: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to create the listener '{listener_str}'. The parameter "
                f"'{parameter_name}' must be of type '{parameter_type}' in the "
                f"listener's provided parameters."
            ),
        )
