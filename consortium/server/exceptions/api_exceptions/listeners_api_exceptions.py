"""
Exception hierarchy for the REST API endpoint at /api/listeners.

- BaseAPIException: Base class for all API-related exceptions.
 - HTTPError: Base class for all HTTP-related exceptions.
   - NotFoundError: Raised when a requested resource is not found.
     - ListenerNotFoundError: Raised when a requested listener is not found.
   - ConflictError: Raised when an operation cannot be completed due to a conflict with
   the current state of the resource.
     - ListenerAlreadyRunningError: Raised when an attempt is made to start an already
     running listener.
     - ListenerNotRunningError: Raised when an attempt is made to stop or cancel a
     listener that is not running.
   - UnprocessableEntityError: Raised when the server cannot process the request due to
   malformed syntax or invalid data.
     - InvalidListenerParameterNameError: Raised when an invalid listener parameter
     name is provided.
     - InvalidListenerParameterValueError: Raised when an invalid listener parameter
     value is provided.
   - InternalServerErrorError: Raised when an internal server error occurs.
     - ListenerTemplateResolutionError: Raised when an error occurs during listener
     template resolution.
   - ListenerStartError: Raised when an error occurs while starting a listener.
   - ListenerStopError: Raised when an error occurs while stopping a listener.
"""

from typing import Any

from consortium.framework.c2_types import BaseListenerType
from consortium.server.exceptions.api_exceptions.base_api_exception import (
    BaseAPIException,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ConflictError,
    InternalServerErrorError,
    NotFoundError,
    UnprocessableEntityError,
)


class ListenerNotFoundError(NotFoundError):
    code = "LISTENER_NOT_FOUND_ERROR"


class InvalidListenerParameterNameError(UnprocessableEntityError):
    code = "INVALID_LISTENER_PARAMETER_NAME_ERROR"


class InvalidListenerParameterValueError(UnprocessableEntityError):
    code = "INVALID_LISTENER_PARAMETER_VALUE_ERROR"


class ListenerAlreadyRunningError(ConflictError):
    code = "LISTENER_ALREADY_RUNNING_ERROR"


class ListenerNotRunningError(ConflictError):
    code = "LISTENER_NOT_RUNNING_ERROR"


class ListenerTemplateResolutionError(InternalServerErrorError):
    code = "LISTENER_TEMPLATE_RESOLUTION_ERROR"

    def __init__(
        self,
        listener_type: BaseListenerType,
    ) -> None:
        super().__init__(
            message=(
                "Failed to resolve the listener's listener template for the given "
                "listener type with listener type ID "
                f'"{listener_type.listener_type_id}".'
            ),
            detail={"listener_type": listener_type.to_json()},
        )


class ListenerStartError(BaseAPIException):
    status_code = 400
    code = "LISTENER_START_ERROR"


class ListenerStopError(BaseAPIException):
    status_code = 400
    code = "LISTENER_STOP_ERROR"
