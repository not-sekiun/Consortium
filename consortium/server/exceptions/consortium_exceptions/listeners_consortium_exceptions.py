"""
Exception hierarchy for listeners errors:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`ListenersError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenersError]
        - [`ListenersFrameworkError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenersFrameworkError]
            - [`ListenerOperationError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerOperationError]
                - [`ListenerStartError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerStartError]
                - [`ListenerRuntimeError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerRuntimeError]
                - [`ListenerStopError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerStopError]
            - [`ListenerStateError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerStateError]
                - [`ListenerNotRunningError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerNotRunningError]
                - [`ListenerAlreadyRunningError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerAlreadyRunningError]
            - [`ListenerCreationError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerCreationError]
                - [`ListenerCreationParameterTypeError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerCreationParameterTypeError]
        - [`ListenersServiceError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenersServiceError]
            - [`ListenerNotFoundError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerNotFoundError]
            - [`ListenerAlreadyExistsError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerAlreadyExistsError]
            - [`ListenerParameterUpdateError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerParameterUpdateError]
                - [`InvalidListenerParameterNameError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.InvalidListenerParameterNameError]
                - [`InvalidListenerParameterValueError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.InvalidListenerParameterValueError]
"""

from typing import Any

from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as comp_excs,
)
from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class ListenersError(BaseConsortiumError):
    """
    Base exception for all listeners-related errors.

    All exceptions that inherit from `ListenersError` define, `code`, `message`, and
    `detail` attributes. For brevity, `message` and `detail` are omitted within
    the documentation here.

    Attributes:
        code: A **stable, machine-readable identifier** for the specific type of
            error that occurred.
        message: A human-readable message that describes the error.
        detail: Any JSON-serializable data structure holding **structured, raw data**
            relevant to the error.
    """

    code = "LISTENER_ERROR"


class ListenersFrameworkError(ListenersError):
    """
    Base exception for all errors that occur within the listeners framework.
    """

    code = "LISTENERS_FRAMEWORK_ERROR"


class ListenerOperationError(
    comp_excs.ComponentOperationError,
    ListenersFrameworkError,
):
    """
    Base exception for all errors that occur during the operation of a particular
    listener.
    """

    code = "LISTENER_OPERATION_ERROR"

    _COMPONENT_TYPE = "listener"


class ListenerStartError(comp_excs.ComponentStartError, ListenerOperationError):
    """
    Raised when a listener fails to start during listener operation.
    """

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


class ListenerRuntimeError(comp_excs.ComponentRuntimeError, ListenerOperationError):
    """
    Raised when a listener encounters an unhandled error at runtime during listener
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


class ListenerStopError(comp_excs.ComponentStopError, ListenerOperationError):
    """
    Raised when a listener fails to stop during listener operation.
    """

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
    ListenersFrameworkError,
    comp_excs.ComponentStateError,
):
    """
    Base exception for all errors that occur due to invalid listener status during
    listener operation.
    """

    code = "LISTENER_STATE_ERROR"

    _COMPONENT_TYPE = "listener"


class ListenerNotRunningError(
    comp_excs.ComponentNotRunningError,
    ListenerStateError,
):
    """
    Raised when an operation is attempted on a listener that requires the listener to
    already be running but the listener is not running.
    """

    code = "LISTENER_NOT_RUNNING_ERROR"

    def __init__(
        self,
        listener_str: str,
    ):
        super().__init__(component_str=listener_str)


class ListenerAlreadyRunningError(
    comp_excs.ComponentAlreadyRunningError,
    ListenerStateError,
):
    """
    Raised when an operation is attempted on a listener that requires the listener to
    not already be started or running but the listener is already started or running.
    """

    code = "LISTENER_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        listener_str: str,
    ):
        super().__init__(component_str=listener_str)


class ListenerCreationError(ListenersFrameworkError):
    """
    Base exception for all errors that occur during the creation of a listener.
    """

    code = "LISTENER_CREATION_ERROR"


class ListenerCreationParameterTypeError(ListenerCreationError):
    """
    Raised when a provided listener parameter is not of the expected type during
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


class ListenersServiceError(ListenersError):
    """
    Base exception for all errors that occur within the listeners service.
    """

    code = "LISTENERS_SERVICE_ERROR"


class ListenerNotFoundError(ListenersServiceError):
    """
    Raised when the requested listener with the provided listener ID was not found in
    the listeners service.
    """

    code = "LISTENER_NOT_FOUND_ERROR"

    def __init__(self, listener_id: str):
        super().__init__(
            f"Failed to find the requested listener. No listener was found with the "
            f"provided listener ID '{listener_id}'.",
        )


class ListenerAlreadyExistsError(ListenersServiceError):
    """
    Raised when attempting to create a listener with a listener ID that already exists
    in the listeners service.
    """

    code = "LISTENER_ALREADY_EXISTS_ERROR"

    def __init__(self, listener_id: str):
        super().__init__(
            message=(
                f"Failed to add the specified listener. A listener already exists with "
                f"the listener ID '{listener_id}'."
            ),
        )


class ListenerParameterUpdateError(ListenersServiceError):
    """
    Base exception for all errors that occur when updating a listener parameter through
    the listeners service.
    """

    code = "LISTENER_PARAMETER_UPDATE_ERROR"


class InvalidListenerParameterNameError(ListenerParameterUpdateError):
    """
    Raised when an invalid parameter name is provided when attempting to update a
    listener parameter through the listeners service.
    """

    code = "INVALID_LISTENER_PARAMETER_NAME_ERROR"

    def __init__(self, listener_str: str, parameter_name: str):
        super().__init__(
            message=(
                f"Failed to update the listener parameter for listener "
                f"'{listener_str}'. The provided parameter name '{parameter_name}' was "
                f"not found for the listener."
            ),
        )


class InvalidListenerParameterValueError(ListenerParameterUpdateError):
    """
    Raised when an invalid parameter value is provided when attempting to update a
    listener parameter through the listeners service.
    """

    code = "INVALID_LISTENER_PARAMETER_VALUE_ERROR"

    def __init__(
        self,
        listener_str: str,
        parameter_name: str,
        parameter_value: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to update the listener parameter for listener "
                f"'{listener_str}'. The value provided '{parameter_value}' for the "
                f"parameter '{parameter_name}' is invalid. {error_message}"
            ),
        )
