from typing import Any

from consortium.framework._core.framework_exceptions import (
    components_framework_exceptions,
)


class ListenersFrameworkError(
    components_framework_exceptions.ComponentsFrameworkError,
):
    """Base exception for all errors that occur within the listeners framework."""

    code = "LISTENERS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "listener"


class ListenerOperationError(
    components_framework_exceptions.ComponentOperationError,
    ListenersFrameworkError,
):
    """Base exception for all errors that occur during the operation of a particular
    listener.
    """

    code = "LISTENER_OPERATION_ERROR"


class ListenerStartError(
    components_framework_exceptions.ComponentStartError, ListenerOperationError
):
    """Raised when a listener fails to start during listener operation."""

    code = "LISTENER_START_ERROR"

    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            component_str=listener_str,
            error_message=error_message,
            detail=detail,
        )


class ListenerRuntimeError(
    components_framework_exceptions.ComponentRuntimeError, ListenerOperationError
):
    """Raised when a listener encounters an unhandled error at runtime during listener
    operation.
    """

    code = "LISTENER_RUNTIME_ERROR"

    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            component_str=listener_str,
            error_message=error_message,
            detail=detail,
        )


class ListenerStopError(
    components_framework_exceptions.ComponentStopError, ListenerOperationError
):
    """Raised when a listener fails to stop during listener operation."""

    code = "LISTENER_STOP_ERROR"

    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            component_str=listener_str,
            error_message=error_message,
            detail=detail,
        )


class ListenerStateError(
    components_framework_exceptions.ComponentStateError,
    ListenersFrameworkError,
):
    """Base exception for all errors that occur due to invalid listener status during
    listener operation.
    """

    code = "LISTENER_STATE_ERROR"


class ListenerNotRunningError(
    components_framework_exceptions.ComponentNotRunningError,
    ListenerStateError,
):
    """Raised when an operation is attempted on a listener that requires the listener to
    already be running but the listener is not running.
    """

    code = "LISTENER_NOT_RUNNING_ERROR"

    def __init__(
        self,
        listener_str: str,
    ):
        super().__init__(component_str=listener_str)


class ListenerAlreadyRunningError(
    components_framework_exceptions.ComponentAlreadyRunningError,
    ListenerStateError,
):
    """Raised when an operation is attempted on a listener that requires the listener to
    not already be started or running but the listener is already started or running.
    """

    code = "LISTENER_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        listener_str: str,
    ):
        super().__init__(component_str=listener_str)


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
