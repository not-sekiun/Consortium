import json
import traceback
from http.client import responses

import jwt
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    InternalServerErrorError,
    ServiceUnavailableError,
)
from consortium.server.objects.server_objects import ServerStatus
from consortium.server.server_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_SECRET_KEY,
)

rest_api_logger = logger.bind(logger_name="Consortium REST API")
users_service = server_singletons.users_service
application_service = server_singletons.application_service


# this middleware checks if the server is in the process of shutting down and if so
# returns an error response with a 503 Service Unavailable status code notifying the
# requester that the server is no longer willing to process any new requests
async def check_if_server_is_shutting_down(
    request: Request,
    call_next,
) -> JSONResponse | Response:
    if server_singletons.server.status == ServerStatus.SHUTTING_DOWN:
        return JSONResponse(
            status_code=ServiceUnavailableError().status_code,
            content=ServiceUnavailableError().to_json(),
        )
    return await call_next(request)


# this middleware checks if the request is authenticated with a valid JSON Web Token. If
# the request is not authenticated, the server will respond with a 401 Unauthorized. The
# only exceptions to this are the /api/login endpoint which depending on whether the
# login is successful or not will return a 200 OK or a 401 Unauthorized response and the
# /docs endpoint for the remote host 127.0.0.1 which is used for the server's Swagger UI
# and does not require authentication
async def check_if_request_is_authenticated(request: Request, call_next) -> Response:
    # TODO: Move this to a service that can be accessed by plugins to hook into the
    #  RBAC system
    # Provide access to the endpoint /api/login for hosts that have yet to authenticate.
    if request.url.path == "/api/login" and request.method == "POST":
        return await call_next(request)
    # Provide access to the automatic documentation endpoints for localhost only.
    elif (
        request.url.path in ("/openapi.json", "/docs", "/redoc")
        and request.client.host == "127.0.0.1"
    ):
        # We manually do a check here to prevent the framework from automatically
        # raising a HTTPException with a 405 status code. Because we have registered
        # custom exception handlers for HTTPException at server_exception_handlers.py,
        # we want to return a manual 405 response here instead of a REST API error JSON
        # response which would be the default behavior upon raising HTTPException with a
        # 405 status code
        if request.method != "GET":
            return Response(status_code=405)
        return await call_next(request)
    else:
        try:
            # if the Authorization header is not present, KeyError is thrown. The header
            # is in lowercase within the headers dictionary of the request object
            auth_header = request.headers["authorization"]
            if not auth_header.startswith("Bearer "):
                return Response(status_code=401)
            # format of the Authorization header is: Bearer <token>
            encoded_json_web_token = auth_header[7:]
            decoded_json_web_token = jwt.decode(
                jwt=encoded_json_web_token,
                key=JSON_WEB_TOKEN_SECRET_KEY,
                algorithms=JSON_WEB_TOKEN_ALGORITHMS,
            )
            access_token = decoded_json_web_token["sub"]
            # check if the user exists in the users service, ie if they are logged in or
            # not. If they are not logged in, this call raises a ValueError
            _ = users_service.get_user_by_access_token(access_token)
        # KeyError: Authorization header is not present
        # IndexError: Authorization header is empty
        # ValueError: User does not exist in the users service
        # jwt.exceptions.InvalidTokenError: JSON Web Token is invalid, base exception
        # for any failure on the decode call for a token
        except (KeyError, IndexError, ValueError, jwt.exceptions.InvalidTokenError):
            return Response(status_code=401)
        return await call_next(request)


# this middleware checks the remote host address against the remote host whitelist or
# blacklist. If the host is not on the whitelist or is on the blacklist, the server will
# respond with an empty 403 Forbidden response
async def check_if_remote_host_is_allowed(request: Request, call_next) -> Response:
    # Note: an empty whitelist does not mean that no one is on the whitelist, rather it
    # means that everyone is permitted.
    if server_singletons.server.server_config.remote_host_whitelist and (
        request.client.host
        not in server_singletons.server.server_config.remote_host_whitelist
    ):
        return Response(status_code=403)
    if server_singletons.server.server_config.remote_host_blacklist and (
        request.client.host
        in server_singletons.server.server_config.remote_host_blacklist
    ):
        return Response(status_code=403)
    return await call_next(request)


# this middleware spoofs the server header to make it appear as if the server is running
# a different web server software (Apache) than it actually is to help prevent C2 server
# fingerprinting. The server header is typically "Server: uvicorn" by default
async def spoof_response_server_header(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["server"] = "Apache"
    return response


# this middleware logs the requests to and responses from the framework's REST API along
# with any internal server errors to the console and to log files located at
# data/server/logs. Because it logs errors, this middleware also acts as a catch-all
# exception handler for any unhandled exceptions that occur within the server and
# returns an error response with a 500 Internal Server Error status code when an
# unhandled exception occurs
async def log_rest_api_requests_and_responses(
    request: Request,
    call_next,
) -> JSONResponse | Response:
    # color map is to map HTTP status codes to their respective ANSI color codes for
    # display in the console
    color_map = {
        "1": ("<bold><blue>", "</></>"),
        "2": ("<bold><green>", "</></>"),
        "3": ("<bold><blue>", "</></>"),
        "4": ("<bold><yellow>", "</></>"),
        "5": ("<bold><red>", "</></>"),
    }
    try:
        response = await call_next(request)
        format_string = (
            "{}:{} <bold><blue>{}</></> {} - "
            + color_map[str(response.status_code)[0]][0]
            + "{} {}"
            + color_map[str(response.status_code)[0]][1]
            + " {}"
        )

        if 100 <= response.status_code < 400:
            rest_api_log_function = rest_api_logger.opt(ansi=True).info
        elif 400 <= response.status_code < 500:
            rest_api_log_function = rest_api_logger.opt(ansi=True).warning
        elif 500 <= response.status_code < 600:
            rest_api_log_function = rest_api_logger.opt(ansi=True).error
        else:
            raise ValueError("Invalid HTTP status code")

        rest_api_log_function(
            format_string,
            request.client.host,
            request.client.port,
            request.method,
            request.url.path,
            response.status_code,
            responses[response.status_code],
            response.headers["content-length"],
        )

        return response
    except Exception:
        rest_api_logger.opt(ansi=True).error(
            (
                "{}:{} <bold><blue>{}</></> {} - <bold><red>500 Internal Server Error"
                "</></> {}"
            ),
            request.client.host,
            request.client.port,
            request.method,
            request.url.path,
            # length of the response as a JSON string
            len(json.dumps(InternalServerErrorError().to_json())),
        )
        rest_api_logger.opt(ansi=True).error(
            "<bold><red>{}</></>",
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=InternalServerErrorError().status_code,
            content=InternalServerErrorError().to_json(),
        )
