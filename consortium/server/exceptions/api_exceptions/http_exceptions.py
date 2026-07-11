from pydantic import JsonValue

from consortium.server.exceptions.api_exceptions.base_api_exception import (
    BaseAPIError,
)


class HTTPError(BaseAPIError):
    status_code = 500
    code = "HTTP_ERROR"


class ForbiddenError(HTTPError):
    status_code = 403
    code = "FORBIDDEN_ERROR"

    def __init__(
        self,
        message: str = "You do not have permission to access this resource.",
        detail: dict[str, JsonValue] | None = None,
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
        detail: dict[str, JsonValue] | None = None,
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
        detail: dict[str, JsonValue] | None = None,
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
        detail: dict[str, JsonValue] | None = None,
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
        detail: dict[str, JsonValue] | None = None,
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
        detail: dict[str, JsonValue] | None = None,
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
        detail: dict[str, JsonValue] | None = None,
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
        detail: dict[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
