# HTTP related errors that are not specific to any api endpoint. These errors are
# raised internally by the FastAPI framework and are not raised by the application
# code. They are included here to provide additional data for preprocessing in the
# custom defined server exception handlers at server_exception_handlers.py.
# - BaseAPIException: Raised when an error occurs in the server's REST API
#   - HTTPError: Raised when a generic HTTP related error occurs that is not specific to any API endpoint
#     - UnauthorizedHTTPError: Raised when a user is not authorized to access a resource (401 Unauthorized)
#     - ForbiddenHTTPError: Raised when a user does not have permission to access a resource (403 Forbidden)
#     - NotFoundHTTPError: Raised when a requested resource could not be found (404 Not Found)
#     - MethodNotAllowedHTTPError: Raised when a requested method is not allowed for a resource (405 Method Not Allowed)
#     - UnprocessableEntityHTTPError: Raised when a request could not be processed due to invalidly formatted data (422 Unprocessable Entity)
#     - InternalServerErrorHTTPError: Raised when an internal server error occurs (500 Internal Server Error)
#     - ServiceUnavailableHTTPError: Raised when a service is unavailable (503 Service Unavailable)
from typing import Any, Type

from pydantic import BaseModel, create_model

from consortium.server.exceptions.api_exceptions.base_api_exception import (
    BaseAPIException,
)


class HTTPError(BaseAPIException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str = "",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


# UnauthorizedHTTPError is a special error whose to_json() method returns None. This is
# so that the JSON data returned as part of the response body is empty to prevent C2
# server fingerprinting from unauthorized clients.
class UnauthorizedHTTPError(HTTPError):
    def __init__(
        self,
        status_code: int = 401,
        code: str = "UNAUTHORIZED_ERROR",
        message: str = "Unauthorized",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )

    def to_json(self) -> None:
        return None

    def to_pydantic_model(self) -> Type[BaseModel]:
        # Make the pydantic model show an empty example in the OpenAPI docs to
        # demonstrate that the server sends an empty response body for this error.
        model = create_model(
            f"{self.__class__.__name__}Model",
        )
        model.model_config = {"json_schema_extra": {"example": ""}}
        return model


class ForbiddenHTTPError(HTTPError):
    def __init__(
        self,
        status_code: int = 403,
        code: str = "FORBIDDEN_ERROR",
        message: str = "You do not have permission to access this resource.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class NotFoundHTTPError(HTTPError):
    def __init__(
        self,
        status_code: int = 404,
        code: str = "NOT_FOUND_ERROR",
        message: str = "The requested resource could not be found.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class MethodNotAllowedHTTPError(HTTPError):
    def __init__(
        self,
        status_code: int = 405,
        code: str = "METHOD_NOT_ALLOWED_ERROR",
        message: str = "The requested method is not allowed for this resource.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class UnprocessableEntityHTTPError(HTTPError):
    def __init__(
        self,
        status_code: int = 422,
        code: str = "UNPROCESSABLE_ENTITY_ERROR",
        message: str = (
            "The request could not be processed due to it containing invalidly "
            "formatted data."
        ),
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class InternalServerErrorHTTPError(HTTPError):
    def __init__(
        self,
        status_code: int = 500,
        code: str = "INTERNAL_SERVER_ERROR",
        message: str = "An internal server error occurred. Please try again later.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class ServiceUnavailableHTTPError(HTTPError):
    def __init__(
        self,
        status_code: int = 503,
        code: str = "SERVICE_UNAVAILABLE_ERROR",
        message: str = "The service is currently unavailable. Please try again later.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )
