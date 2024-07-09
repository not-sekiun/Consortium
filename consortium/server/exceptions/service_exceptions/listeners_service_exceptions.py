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
    pass


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


class ListenerOperationError(ListenersServiceError):
    pass


class ListenerStartError(ListenerOperationError):
    pass


class ListenerStopError(ListenerOperationError):
    pass


class ListenerStateError(ListenersServiceError):
    pass


class ListenerAlreadyRunningError(ListenerStateError):
    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the listener. The listener "
            "is already running which conflicts with the operation that was requested."
        ),
    ):
        super().__init__(message)


class ListenerNotRunningError(ListenerStateError):
    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the listener. The listener "
            "is not running which conflicts with the operation that was requested."
        ),
    ):
        super().__init__(message)


class ListenerParameterUpdateError(ListenersServiceError):
    pass


class InvalidListenerParameterNameError(ListenerParameterUpdateError):
    def __init__(self, parameter_name: str, listener: str):
        super().__init__(
            f"Failed to update listener parameters for listener '{listener}'. The "
            f"provided parameter name '{parameter_name}' was not found for the "
            f"listener.",
        )


class InvalidListenerParameterValueError(ListenerParameterUpdateError):
    def __init__(
        self,
        parameter_name: str,
        parameter_value: str,
        listener: str,
        validation_error_message: str,
    ):
        super().__init__(
            f"Failed to update listener parameters for listener '{listener}'. The "
            f"provided parameter value '{parameter_value}' failed validation for the "
            f"parameter '{parameter_name}': {validation_error_message}",
        )
