# HTTP related errors that are not specific to any api endpoint. These errors are raised
# internally by the FastAPI framework and are not raised by the application code. They
# are included here to provide additional data for preprocessing in the custom defined
# server exception handlers at server_exception_handlers.py.
# - HTTPError
#   - ForbiddenError
#   - NotFoundError
#     - UserAccountNotFoundError
#     - ListenerTemplateNotFoundError
#     - ListenerNotFoundError
#     - AgentTemplateNotFoundError
#     - AgentGeneratorNotFoundError
#     - UserNotFoundError
#     - AgentNotFoundError
#   - MethodNotAllowedError
#   - UnprocessableEntityError
#   - InternalServerError
#   - ServiceUnavailableError
from typing import Any, Type

from pydantic import BaseModel, create_model

from consortium.server.exceptions.base_server_exception import BaseServerException


class HTTPError(BaseServerException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str = "",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


# UnauthorizedError is a special error that has no response body to prevent C2 server
# fingerprinting from unauthorized hosts. This error does not inherit from
# ServerException because it exists solely as an exception model to be documented in
# the OpenAPI schema.
class UnauthorizedError(BaseServerException):
    def __init__(
        self,
        status_code: int = 401,
        code: str = "UNAUTHORIZED_ERROR",
        message: str = "Unauthorized",
        detail: Any = None,
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
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class NotFoundError(BaseServerException):
    def __init__(
        self,
        status_code: int = 404,
        code: str = "NOT_FOUND_ERROR",
        message: str = "The requested resource could not be found.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class MethodNotAllowedError(BaseServerException):
    def __init__(
        self,
        status_code: int = 405,
        code: str = "METHOD_NOT_ALLOWED_ERROR",
        message: str = "The requested method is not allowed for this resource.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class UnprocessableEntityError(BaseServerException):
    def __init__(
        self,
        status_code: int = 422,
        code: str = "UNPROCESSABLE_ENTITY_ERROR",
        message: str = (
            "The request could not be processed due to it containing invalidly "
            "formatted data."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class InternalServerError(BaseServerException):
    def __init__(
        self,
        status_code: int = 500,
        code: str = "INTERNAL_SERVER_ERROR",
        message: str = "An internal server error occurred. Please try again later.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class ServiceUnavailableError(BaseServerException):
    def __init__(
        self,
        status_code: int = 503,
        code: str = "SERVICE_UNAVAILABLE_ERROR",
        message: str = "The service is currently unavailable. Please try again later.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )
