from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from consortium.server.exceptions.api_exceptions.base_api_exception import (
    BaseAPIError,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    NotFoundError,
    TooManyRequestsError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.server_dependencies import is_user_logged_in


# There isn't a good way to add exception handlers from a separate file, so this is a
# decent workaround (https://github.com/tiangolo/fastapi/discussions/7738)
def register_server_exception_handlers(app: FastAPI) -> None:
    # This exception handler handles the `HTTPExceptions` that the FastAPI framework
    # raises internally on its own to ensure that they conform to our specifications. To
    # handle `HTTPExceptions` raised by FastAPI we need to use the Starlette
    # `HTTPException` class instead of the FastAPI `HTTPException` class
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse | Response:
        # 429 is in here for slowapi's `RateLimitExceeded`, which subclasses Starlette's
        # `HTTPException` and so lands in this handler like any status FastAPI raises
        # itself. Mapping it is what turns a tripped rate limit into a 429 carrying the
        # standard error body: without an entry it fell through to the `ValueError` below
        # and reached the caller as a bare 500. The rate limit's own detail (the limit
        # string, "20 per 1 minute") is deliberately dropped in favour of the generic
        # message, in keeping with every other entry here, so a caller cannot map out the
        # server's limits by tripping them.
        error_code_map = {
            403: ForbiddenError(),
            404: NotFoundError(),
            405: MethodNotAllowedError(),
            429: TooManyRequestsError(),
            500: InternalServerError(),
        }
        # Handle the special case of errors that arise on the /api/login endpoint. Any
        # error that arises on the /api/login endpoint is disguised as a 401
        # Unauthorized error with an empty Response body for unauthorized requests. This
        # is done to prevent C2 server fingerprinting. That includes login's own rate
        # limit: this check runs before the map below, so a caller who trips it is told
        # only that it is unauthorized, and cannot tell a wrong password from a limit
        # they have hit. Every other endpoint reports the limit as the 429 it is.
        if request.url.path == "/api/login" and not is_user_logged_in(request):
            return Response(status_code=401)

        # reformat errors into our specified error response structure
        if exc.status_code in error_code_map:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_code_map[exc.status_code].to_json(),
                headers=exc.headers,
            )
        else:
            raise ValueError(f"Unhandled FastAPI HTTPException: {exc}")

    # This exception handler handles the RequestValidationErrors that are raised by
    # FastAPI internally when a request fails to validate against the pydantic request
    # model.
    @app.exception_handler(FastAPIRequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: FastAPIRequestValidationError,
    ) -> JSONResponse | Response:
        # Handle the special case of errors that arise on the /api/login endpoint. Any
        # error that arises on the /api/login endpoint is disguised as a 401
        # Unauthorized error with an empty Response body. This is done to prevent C2
        # server fingerprinting.
        if request.url.path == "/api/login":
            return Response(status_code=401)

        # Pydantic validation errors for invalid UUID4 strings throw a 422 Unprocessable
        # Entity error with an extremely ugly error message for otherwise benign actions
        # like querying for a resource by ID. To improve usability, we reformat the
        # validation error into our specified error response structure.
        for err in exc.errors():
            if err["type"] == "uuid_parsing":
                loc = err.get("loc", [])
                if loc and loc[0] == "path":
                    # loc[1] is the name of the path parameter
                    param_name = loc[1] if len(loc) > 1 else None
                    path_param_to_resource_name_map = {
                        "user_account_id": "user account",
                        "user_id": "user",
                        "listener_template_id": "listener template",
                        "listener_id": "listener",
                        "agent_template_id": "agent template",
                        "agent_generator_id": "agent generator",
                        "task_id": "task",
                        "result_id": "result",
                        "agent_id": "agent",
                        "resource_id": "resource",
                    }
                    resource_name = path_param_to_resource_name_map.get(
                        param_name,
                        "resource",
                    )
                    raise InvalidUUIDError(
                        resource_name=resource_name,
                        uuid_value=err["input"],
                    ) from None

        return JSONResponse(
            status_code=422,
            content=UnprocessableEntityError(
                detail={"validation_errors": exc.errors()}
            ).to_json(),
        )

    # All the custom exceptions that contain the error data to return to the client
    # inherit from BaseAPIError, so we can use this exception handler to handle all
    # of them at once
    @app.exception_handler(BaseAPIError)
    async def generic_error_exception_handler(
        request: Request,
        exc: BaseAPIError,
    ) -> JSONResponse | Response:
        # Handle the special case of errors that arise on the /api/login endpoint. Any
        # error that arises on the /api/login endpoint is disguised as a 401
        # Unauthorized error with an empty Response body. This is done to prevent C2
        # server fingerprinting.
        if request.url.path == "/api/login":
            return Response(status_code=401)
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_json(),
            headers=exc.headers,
        )
