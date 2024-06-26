"""
Exception hierarchy for the REST API endpoint at /api/listeners.

- BaseAPIException: Base class for all API-related exceptions.
 - HTTPError: Base class for all HTTP-related exceptions.
   - NotFoundError: Raised when a requested resource is not found.
     - ListenerNotFoundError: Raised when a requested listener is not found.
   - InternalServerErrorError: Raised when an internal server error occurs.
     - ListenerTemplateResolutionError: Raised when an error occurs during listener
     template resolution.
   - UnprocessableEntityError: Raised when the server cannot process the request due to
   malformed syntax or invalid data.
     - ListenerParameterUpdateError: Raised when an error occurs while updating
     listener parameters.
       - InvalidListenerParameterNameError: Raised when an invalid listener parameter
       name is provided.
       - InvalidListenerParameterValueError: Raised when an invalid listener parameter
       value is provided.
 - ListenerError: Base class for all exceptions related to the listener API.
   - ListenerStateError: Raised when an error occurs related to the listener's state.
     - ListenerAlreadyRunningError: Raised when an attempt is made to start an already
     running listener.
     - ListenerNotRunningError: Raised when an attempt is made to stop or cancel a
     listener that is not running.
   - ListenerOperationError: Raised when an error occurs during listener operations.
     - ListenerStartError: Raised when an error occurs while starting a listener.
     - ListenerStopError: Raised when an error occurs while stopping a listener.
     - ListenerCancellationError: Raised when an error occurs while cancelling a
     listener.
"""

from typing import Any

from consortium.server.exceptions.api_exceptions.base_api_exception import (
    BaseAPIException,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    InternalServerErrorError,
    NotFoundError,
    UnprocessableEntityError,
)
from consortium.server.framework.c2_types import ListenerType


class ListenerNotFoundError(NotFoundError):
    def __init__(
        self,
        listener_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="LISTENER_NOT_FOUND_ERROR",
            message=(
                f'The requested listener with the provided listener ID "{listener_id}" '
                "was not found."
            ),
            detail={"listener_id": listener_id},
        )


class ListenerTemplateResolutionError(InternalServerErrorError):
    def __init__(
        self,
        listener_type: ListenerType,
    ) -> None:
        super().__init__(
            status_code=500,
            code="LISTENER_TEMPLATE_RESOLUTION_ERROR",
            message=(
                "Failed to resolve the listener's listener template for the given "
                "listener type with listener type ID "
                f'"{listener_type.listener_type_id}".'
            ),
            detail={"listener_type": listener_type.to_json()},
        )


class ListenerError(BaseAPIException):
    def __init__(
        self,
        status_code: int = 400,
        code: str = "LISTENER_ERROR",
        message: str = "A listener error occurred.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class ListenerStateError(ListenerError):
    def __init__(
        self,
        status_code: int = 409,
        code: str = "LISTENER_STATE_ERROR",
        message: str = (
            "A listener error occurred due to a conflict in the listener's state."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class ListenerAlreadyRunningError(ListenerStateError):
    def __init__(
        self,
        message: str = (
            "The listener is already running. Stop it before performing this operation."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=409,
            code="LISTENER_ALREADY_RUNNING_ERROR",
            message=message,
            detail=detail,
        )


class ListenerNotRunningError(BaseAPIException):
    def __init__(
        self,
        message: str = (
            "The listener is not running. Start it before performing this operation."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=409,
            code="LISTENER_NOT_RUNNING_ERROR",
            message=message,
            detail=detail,
        )


class ListenerOperationError(ListenerError):
    def __init__(
        self,
        status_code: int = 400,
        code: str = "LISTENER_OPERATION_ERROR",
        message: str = "A listener error occurred while it was in operation.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class ListenerStartError(ListenerOperationError):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="LISTENER_START_ERROR",
            message=message,
            detail=detail,
        )


class ListenerStopError(ListenerOperationError):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="LISTENER_STOP_ERROR",
            message=message,
            detail=detail,
        )


class ListenerCancellationError(ListenerOperationError):
    def __init__(
        self,
        message: str = "An error occurred while attempting to cancel the listener.",
        detail: Any = None,
    ):
        super().__init__(
            status_code=400,
            code="LISTENER_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )


class ListenerParameterUpdateError(UnprocessableEntityError):
    def __init__(
        self,
        status_code: int = 422,
        code: str = "LISTENER_PARAMETER_UPDATE_ERROR",
        message: str = (
            "An error occurred while attempting to update the listener's parameters."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class InvalidListenerParameterNameError(ListenerParameterUpdateError):
    def __init__(
        self,
        parameter_name: str,
    ) -> None:
        super().__init__(
            status_code=422,
            code="INVALID_LISTENER_PARAMETER_NAME_ERROR",
            message=(
                f'The provided listener parameter name "{parameter_name}" is '
                "invalid."
            ),
            detail={"parameter_name": parameter_name},
        )


class InvalidListenerParameterValueError(ListenerParameterUpdateError):
    def __init__(
        self,
        parameter_name: str,
        parameter_value: Any,
        exception: Exception,
    ) -> None:
        super().__init__(
            status_code=422,
            code="INVALID_LISTENER_PARAMETER_VALUE_ERROR",
            message=(
                f'The provided listener parameter value "{parameter_value}" for '
                f'parameter "{parameter_name}" is invalid.'
            ),
            detail={
                "parameter_name": parameter_name,
                "parameter_value": parameter_value,
                "exception": str(exception),
            },
        )
