"""
Exception hierarchy for the listeners service:

- BaseServiceException: Base class for all exceptions raised by services.
  - ListenersServiceError: Base class for all exceptions raised by the listeners
    service.
    - ListenerNotFoundError: Raised when a requested listener is not found.
    - ListenerAlreadyExistsError: Raised when attempting to add a listener that
      already exists.
    - ListenerOperationError: Base class for errors related to listener operations.
      - ListenerStartError: Raised when there's an error starting a listener.
      - ListenerStopError: Raised when there's an error stopping a listener.
    - ListenerStateError: Base class for errors related to listener state.
      - ListenerAlreadyRunningError: Raised when attempting an operation on an
        already running listener.
      - ListenerNotRunningError: Raised when attempting an operation on a non-running
        listener.
    - ListenerParameterUpdateError: Base class for errors related to updating listener
      parameters.
      - InvalidListenerParameterNameError: Raised when an invalid parameter name is
        provided.
      - InvalidListenerParameterValueError: Raised when an invalid parameter value is
        provided.
    - ListenerCreationError: Base class for errors related to listener creation.
      - ListenerTemplateOptionNotFoundError: Raised when a specified option is not
        found in the listener template.
      - ListenerTemplateOptionValueError: Raised when an invalid value is provided for
        a listener template option.
"""

from typing import Any

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class ListenersServiceError(BaseServiceException):
    code = "LISTENERS_SERVICE_ERROR"


class ListenerNotFoundError(ListenersServiceError):
    code = "LISTENER_NOT_FOUND_ERROR"

    def __init__(self, listener_id: str):
        super().__init__(
            f"Failed to find the requested listener. No listener was found with the "
            f"provided listener ID '{listener_id}'.",
        )


class ListenerAlreadyExistsError(ListenersServiceError):
    code = "LISTENER_ALREADY_EXISTS_ERROR"

    def __init__(self, listener_id: str):
        super().__init__(
            message=(
                f"Failed to add the specified listener. A listener already exists with "
                f"the listener ID '{listener_id}'."
            ),
        )


class ListenerOperationError(ListenersServiceError):
    code = "LISTENER_OPERATION_ERROR"

    def __init__(self, message: str = "", detail: Any = None):
        super().__init__(message=message, detail=detail)


class ListenerStartError(ListenerOperationError):
    code = "LISTENER_START_ERROR"


class ListenerStopError(ListenerOperationError):
    code = "LISTENER_STOP_ERROR"


class ListenerStateError(ListenersServiceError):
    code = "LISTENER_STATE_ERROR"


class ListenerAlreadyRunningError(ListenerStateError):
    code = "LISTENER_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the listener. The listener "
            "is already running which conflicts with the operation that was requested."
        ),
    ):
        super().__init__(message=message)


class ListenerNotRunningError(ListenerStateError):
    code = "LISTENER_NOT_RUNNING_ERROR"

    def __init__(
        self,
        message: str = (
            "Failed to perform the requested operation on the listener. The listener "
            "is not running which conflicts with the operation that was requested."
        ),
    ):
        super().__init__(message=message)


class ListenerParameterUpdateError(ListenersServiceError):
    code = "LISTENER_PARAMETER_UPDATE_ERROR"


class InvalidListenerParameterNameError(ListenerParameterUpdateError):
    code = "INVALID_LISTENER_PARAMETER_NAME_ERROR"

    def __init__(self, listener_str: str, parameter_name: str):
        super().__init__(
            message=(
                f"Failed to update listener parameters for listener '{listener_str}'. The "
                f"provided parameter name '{parameter_name}' was not found for the "
                f"listener."
            ),
        )


class InvalidListenerParameterValueError(ListenerParameterUpdateError):
    code = "INVALID_LISTENER_PARAMETER_VALUE_ERROR"

    def __init__(
        self,
        listener_str: str,
        parameter_name: str,
        parameter_value: str,
        validation_error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to update listener parameters for listener '{listener_str}'. The "
                f"provided parameter value '{parameter_value}' failed validation for "
                f"the parameter '{parameter_name}': {validation_error_message}"
            ),
        )


class ListenerCreationError(ListenersServiceError):
    code = "LISTENER_CREATION_ERROR"

    def __init__(self, message: str = "", detail: Any = None):
        super().__init__(message=message, detail=detail)


# This is a wrapper exception for ListenerTemplateOptionNotFoundError from the listener
# templates framework exceptions. It just needs to pass on the message and detail data
# from that exception.
class ListenerTemplateOptionNotFoundError(ListenerCreationError):
    code = "LISTENER_TEMPLATE_OPTION_NOT_FOUND_ERROR"


# This is a wrapper exception for ListenerTemplateOptionValueError from the listener
# templates framework exceptions. It just needs to pass on the message and detail data
# from that exception.
class ListenerTemplateOptionValueError(ListenerCreationError):
    code = "LISTENER_TEMPLATE_OPTION_VALUE_ERROR"
