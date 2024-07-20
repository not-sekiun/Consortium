"""
Exception hierarchy for the listeners service:

- BaseServiceException: Base class for all exceptions raised by services.
  - ListenersServiceError: Base class for all exceptions raised by the listeners service.
    - ListenerNotFoundError: Raised when a requested listener is not found.
    - ListenerAlreadyExistsError: Raised when attempting to add a listener that already
    exists.
    - ListenerOperationError: Base class for errors related to listener operations.
      - ListenerStartError: Raised when there's an error starting a listener.
      - ListenerStopError: Raised when there's an error stopping a listener.
    - ListenerStateError: Base class for errors related to listener state.
      - ListenerAlreadyRunningError: Raised when attempting an operation on an already
      running listener.
      - ListenerNotRunningError: Raised when attempting an operation on a non-running
      listener.
    - ListenerParameterUpdateError: Base class for errors related to updating listener
    parameters.
      - InvalidListenerParameterNameError: Raised when an invalid parameter name is
      provided.
      - InvalidListenerParameterValueError: Raised when an invalid parameter value is
      provided.
"""

from typing import Any

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
            message=(
                f"Failed to add the specified listener. A listener already exists with "
                f"the listener ID '{listener_id}'."
            ),
        )


class ListenerOperationError(ListenersServiceError):
    def __init__(self, message: str = "", detail: Any = None):
        self.detail = detail
        super().__init__(message=message)


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
        super().__init__(message=message)


class ListenerNotRunningError(ListenerStateError):
    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the listener. The listener "
            "is not running which conflicts with the operation that was requested."
        ),
    ):
        super().__init__(message=message)


class ListenerParameterUpdateError(ListenersServiceError):
    pass


class InvalidListenerParameterNameError(ListenerParameterUpdateError):
    def __init__(self, parameter_name: str, listener: str):
        super().__init__(
            message=(
                f"Failed to update listener parameters for listener '{listener}'. The "
                f"provided parameter name '{parameter_name}' was not found for the "
                f"listener."
            ),
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
            message=(
                f"Failed to update listener parameters for listener '{listener}'. The "
                f"provided parameter value '{parameter_value}' failed validation for "
                f"the parameter '{parameter_name}': {validation_error_message}"
            ),
        )
