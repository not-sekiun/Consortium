from typing import Any

from pydantic import BaseModel, create_model

from consortium.server.exceptions.api_exceptions.base_api_exception import (
    BaseAPIError,
)


class HTTPError(BaseAPIError):
    status_code = 500
    code = "HTTP_ERROR"


# FIXME: Btw this can cause a subtle but not necessarily fatal bug for clients that
#   expect a JSON response body for all error responses. If a client gets a 401 Unauthorized response with an empty
#   body, it may raise an exception when trying to parse the empty body as JSON. This is
#   especially relevant for the CLI client which expects JSON responses for all API
#   calls. We should ensure that the CLI client can gracefully handle this case. But this
#   bug only really pops up if a logged in client is unexpectedly logged out (e.g. due to
#   session expiration) and then makes an API call that requires authentication. So its low
#   priority to fix this client-side issue.
# UnauthorizedError is a special error whose `to_json()` method returns None. This is
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
        "current status of the resource.",
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
