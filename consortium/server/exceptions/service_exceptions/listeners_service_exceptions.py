"""
- BaseServiceException: Base class for all exceptions raised by the listeners service.
  - ListenersServiceError: Base class for all exceptions raised by the listeners service.
    - ListenerNotFoundError: Listener not found.
    - ListenerAlreadyExistsError: Listener already exists.
    - ListenerParameterUpdateError:
      - InvalidListenerParameterNameError:
      - InvalidListenerParameterValueError:
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class ListenersServiceError(BaseServiceException):
    def __init__(self, message: str = "An error occurred in the listeners service."):
        super().__init__(message)


class ListenerNotFoundError(ListenersServiceError):
    def __init__(self, listener_id: str):
        super().__init__(
            f"Failed to find the requested listener. No listener was found with the "
            f"provided listener ID '{listener_id}'.",
        )


class ListenerAlreadyExistsError(ListenersServiceError):
    def __init__(self, listener_id: str):
        super().__init__(
            f"Failed to add the specified listener. A listener already exists with the "
            f"listener ID '{listener_id}'.",
        )


class ListenerTemplateResolutionError(ListenersServiceError):
    def __init__(self, message: str = "", *args):
        super().__init__(message, *args)


class ListenerOperationError(ListenersServiceError):
    def __init__(self, message: str = "", *args):
        super().__init__(message, *args)


class ListenerStartError(ListenerOperationError):
    def __init__(self, message: str = "", *args):
        super().__init__(message, *args)


class ListenerStopError(ListenerOperationError):
    def __init__(self, message: str = "", *args):
        super().__init__(message, *args)


class ListenerStateError(ListenersServiceError):
    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the listener due to a "
            "conflict with the requested operation and the listener's current state."
        )
    ):
        super().__init__(message)


class ListenerAlreadyRunningError(ListenerStateError):
    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the listener. The listener "
            "is already running which conflicts with the operation that was requested."
        )
    ):
        super().__init__(message)


class ListenerNotRunningError(ListenerStateError):
    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the listener. The listener "
            "is not running which conflicts with the operation that was requested."
        )
    ):
        super().__init__(message)


class ListenerParameterUpdateError(ListenersServiceError):
    def __init__(
        self,
        message: str = "Failed to update listener parameter.",
    ):
        super().__init__(message)


class InvalidListenerParameterNameError(ListenerParameterUpdateError):
    def __init__(self, parameter_name: str, listener_string: str):
        super().__init__(
            "Failed to update listener parameter. The provided parameter name "
            f"'{parameter_name}' is not a valid parameter name for the listener "
            f"'{listener_string}'.",
        )


class InvalidListenerParameterValueError(ListenerParameterUpdateError):
    def __init__(
        self,
        parameter_name: str,
        parameter_value_string: str,
        listener_string: str,
        error_message: str,
    ):
        super().__init__(
            "Failed to update listener parameter. The provided parameter value "
            f"'{parameter_value_string}' failed validation for the parameter "
            f"'{parameter_name}' for listener '{listener_string}': {error_message}",
        )
