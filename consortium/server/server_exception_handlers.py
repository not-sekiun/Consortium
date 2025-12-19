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
    UnprocessableEntityError,
)
from consortium.server.server_dependencies import is_user_logged_in


# there isn't a good way to add exception handlers from a separate file, so this is a
# decent workaround (https://github.com/tiangolo/fastapi/discussions/7738)
def register_server_exception_handlers(app: FastAPI) -> None:
    # This exception handler handles the HTTPExceptions that the FastAPI framework
    # raises internally on its own to ensure that they conform to our specifications. To
    # handle HTTPExceptions raised by FastAPI we need to use the Starlette HTTPException
    # class instead of the FastAPI HTTPException class
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse | Response:
        error_code_map = {
            403: ForbiddenError(),
            404: NotFoundError(),
            405: MethodNotAllowedError(),
            500: InternalServerError(),
        }
        # Handle the special case of errors that arise on the /api/login endpoint. Any
        # error that arises on the /api/login endpoint is disguised as a 401
        # Unauthorized error with an empty Response body for unauthorized requests. This
        # is done to prevent C2 server fingerprinting.
        if request.url.path == "/api/login" and not is_user_logged_in(request):
            return Response(status_code=401)

        # reformat errors into our specified error response structure
        if exc.status_code in error_code_map:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_code_map[exc.status_code].to_json(),
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

        return JSONResponse(
            status_code=422,
            content=UnprocessableEntityError(detail=exc.errors()).to_json(),
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
