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


# UnauthorizedError is a special error whose to_json() method returns None. This is
# so that the JSON data returned as part of the response body is empty to prevent C2
# server fingerprinting from unauthorized clients.
class UnauthorizedError(HTTPError):
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


class ForbiddenError(HTTPError):
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


class NotFoundError(HTTPError):
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


class MethodNotAllowedError(HTTPError):
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


class UnprocessableEntityError(HTTPError):
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


class InternalServerErrorError(HTTPError):
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


class ServiceUnavailableError(HTTPError):
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
