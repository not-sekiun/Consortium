"""
HTTP related errors that are not specific to any api endpoint. These errors are raised
internally by the FastAPI framework and are not raised by the application code. They
are included here to provide additional data for preprocessing in the custom defined
server exception handlers at server_exception_handlers.py.
- BaseAPIException: Base class for all API exceptions.
 - HTTPError: Generic HTTP error.
   - UnauthorizedError: User not authorized to access resource (401 Unauthorized).
   - ForbiddenError: User does not have permission to access resource (403 Forbidden).
   - NotFoundError: Requested resource not found (404 Not Found).
   - MethodNotAllowedError: Requested method not allowed for resource (405 Method Not
   Allowed).
   - UnprocessableEntityError: Request could not be processed due to invalid data (422
   Unprocessable Entity).
   - InternalServerErrorError: Internal server error occurred (500 Internal Server
   Error).
   - ServiceUnavailableError: Service is currently unavailable (503 Service
   Unavailable).
"""

from typing import Any

from pydantic import BaseModel, create_model

from consortium.server.exceptions.api_exceptions.base_api_exception import (
    BaseAPIException,
)


class HTTPError(BaseAPIException):
    status_code = 500
    code = "HTTP_ERROR"


# UnauthorizedError is a special error whose to_json() method returns None. This is
# so that the JSON data returned as part of the response body is empty to prevent C2
# server fingerprinting from unauthorized clients.
class UnauthorizedError(HTTPError):
    status_code = 401
    code = "UNAUTHORIZED_ERROR"

    def __init__(
        self,
        message: str = "Unauthorized",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )

    def to_json(self) -> None:
        return None

    def to_pydantic_model(self) -> type[BaseModel]:
        # Make the pydantic model show an empty example in the OpenAPI docs to
        # demonstrate that the server sends an empty response body for this error.
        model = create_model(
            f"{self.__class__.__name__}Model",
        )
        model.model_config = {"json_schema_extra": {"example": ""}}
        return model


class ForbiddenError(HTTPError):
    status_code = 403
    code = "FORBIDDEN_ERROR"

    def __init__(
        self,
        message: str = "You do not have permission to access this resource.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class NotFoundError(HTTPError):
    status_code = 404
    code = "NOT_FOUND_ERROR"

    def __init__(
        self,
        message: str = "The requested resource could not be found.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class MethodNotAllowedError(HTTPError):
    status_code = 405
    code = "METHOD_NOT_ALLOWED_ERROR"

    def __init__(
        self,
        message: str = "The requested method is not allowed for this resource.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class ConflictError(HTTPError):
    status_code = 409
    code = "CONFLICT_ERROR"

    def __init__(
        self,
        message: str = "The request could not be completed due to a conflict with the "
        "current state of the resource.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class UnsupportedMediaTypeError(HTTPError):
    status_code = 415
    code = "UNSUPPORTED_MEDIA_TYPE_ERROR"

    def __init__(
        self,
        message: str = "The request could not be completed due to an unsupported media "
        "type being provided.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class UnprocessableEntityError(HTTPError):
    status_code = 422
    code = "UNPROCESSABLE_ENTITY_ERROR"

    def __init__(
        self,
        message: str = (
            "The request could not be processed due to it containing invalidly "
            "formatted data."
        ),
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class InternalServerError(HTTPError):
    status_code = 500
    code = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: str = "An internal server error occurred. Please try again later.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class ServiceUnavailableError(HTTPError):
    status_code = 503
    code = "SERVICE_UNAVAILABLE_ERROR"

    def __init__(
        self,
        message: str = "The service is currently unavailable. Please try again later.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
