from typing import Annotated

import jwt
from fastapi import Depends, Request, WebSocket, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import ForbiddenError
from consortium.server.exceptions.service_exceptions.users_service_exceptions import (
    UserAccessTokenNotFoundError,
)
from consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions import (
    InvalidWebsocketTicketError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.objects.user_objects import User
from consortium.server.server_jwt_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_SECRET_KEY,
)

# The name of the query parameter a websocket handshake presents its ticket in. A query
# parameter is the only place a browser can put a credential on a handshake: it can set
# neither request headers nor a body there.
WEBSOCKET_TICKET_QUERY_PARAMETER = "ticket"

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
_users_service = server_singletons.users_service
_authorization_service = server_singletons.authorization_service
_websocket_tickets_service = server_singletons.websocket_tickets_service

# Bound with the websocket events logger type so that handshake rejection messages keep
# the colorized terminal treatment they had while this logic lived inside events_api.py.
# The logger name is deliberately route agnostic: the helper below serves any websocket
# route, not only the events socket.
_websocket_logger = logger.bind(
    logger_name="Websocket Authentication",
    logger_type=LoggerType.WEBSOCKET_EVENTS_API_LOGGER,
)


# Ordinarily we would use the middleware to check if the user is logged in, but
# specifically for requests to /api/login we need to manually check if the user is
# already authenticated and return an actual error response if they are. We also need to
# take specific action depending on whether the user is logged in or not, hence the
# returning of a boolean over the raising of ForbiddenError.
def is_user_logged_in(
    request: Request,
) -> bool:
    # Since /api/login is the only API  endpoint that does not require a value, neither
    # our middleware nor our authorization dependencies will guarantee the identity of
    # the requester. Therefore, in this API endpoint specifically we need to manually
    # check if the user is already authenticated and return an actual error response.
    try:
        # if the Authorization header is not present, KeyError is thrown. The header
        # is in lowercase within the headers dictionary of the request object
        auth_header = request.headers["authorization"]
        if not auth_header.startswith("Bearer "):
            return False
        # format of the Authorization header is: Bearer <value>
        encoded_json_web_token = auth_header[7:]
        decoded_json_web_token = jwt.decode(
            jwt=encoded_json_web_token,
            key=JSON_WEB_TOKEN_SECRET_KEY,
            algorithms=JSON_WEB_TOKEN_ALGORITHMS,
        )
        access_token = decoded_json_web_token["sub"]
        # check if the user exists in the users service, ie if they are logged in or
        # not. If they are not logged in, this call raises a ValueError
        _ = _users_service.get_user_by_access_token(access_token)
        return True
    # `KeyError`: Authorization header is not present
    # `IndexError`: Authorization header is empty
    # `ValueError`: User does not exist in the users service
    # `jwt.exceptions.InvalidTokenError`: JSON Web Token is invalid, base exception
    # for any failure on the decode call for a value
    # `UserAccessTokenNotFoundError`: Valid JSON Web Token but does not exist in the
    # current set of users
    except (
        KeyError,
        IndexError,
        ValueError,
        jwt.exceptions.InvalidTokenError,
        UserAccessTokenNotFoundError,
    ):
        return False


def get_current_user(
    encoded_json_web_token: Annotated[str, Depends(_oauth2_scheme)],
) -> User:
    # The middleware has already checked if the JSON Web Token is valid ahead of time,
    # so we can safely decode it here without error handling.
    decoded_json_web_token = jwt.decode(
        jwt=encoded_json_web_token,
        key=JSON_WEB_TOKEN_SECRET_KEY,
        algorithms=JSON_WEB_TOKEN_ALGORITHMS,
    )
    access_token = decoded_json_web_token["sub"]
    # The middleware has already checked that the access value is valid ahead of time,
    # so we can safely use it here without error handling.
    return _users_service.get_user_by_access_token(access_token)


class AuthorizeUserRequest:
    def __init__(self, user_permission: UserPermissions):
        self._user_permission = user_permission

    def __call__(
        self,
        user: Annotated[User, Depends(get_current_user)],
    ) -> None:
        if not _authorization_service.has_permission(user.role, self._user_permission):
            raise ForbiddenError


# A websocket route cannot use `get_current_user`/`AuthorizeUserRequest` above: those read
# the JSON Web Token off a `Request`, and no `Request` object exists for a websocket
# endpoint. A handshake also carries its credential by one of two routes (an Authorization
# header, or a ticket in the query string, since a browser can set no headers on a
# handshake), and those two must not drift apart into parallel implementations. Hence this
# helper: it resolves whichever credential was presented into an access token, then
# resolves the user and checks the permission in exactly one place, so every websocket
# route and every credential source is authorized identically.
#
# Raises `WebSocketException` with `WS_1008_POLICY_VIOLATION` on any failure. Every reason
# closes with that same code and nothing distinguishes them to the client: an invalid
# ticket, a missing or malformed header, an unknown user and an insufficient permission are
# all reported alike. The per-reason detail is written to the debug log instead, so
# operators can diagnose a failed handshake without the code becoming an oracle for callers.
def authenticate_websocket_connection(
    websocket: WebSocket,
    user_permission: UserPermissions,
) -> User:
    access_token = _resolve_websocket_access_token(websocket=websocket)

    # Everything from here down is shared by both credential sources on purpose. Resolving
    # the user and checking the permission happens exactly once, so a ticket can never be a
    # way around a check that the header path applies (or the reverse).
    try:
        user = _users_service.get_user_by_access_token(access_token=access_token)
    except UserAccessTokenNotFoundError:
        _websocket_logger.debug(
            "Failed to authorize the WebSocket connection request. The access "
            "value provided was not found.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from None

    if not _authorization_service.has_permission(user.role, user_permission):
        _websocket_logger.debug(
            f"Rejected WebSocket connection attempt because the user '{user}' had "
            f"insufficient permissions.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return user


def _resolve_websocket_access_token(websocket: WebSocket) -> str:
    ticket = websocket.query_params.get(WEBSOCKET_TICKET_QUERY_PARAMETER)
    # Presenting a ticket is a commitment to that ticket: when one is supplied it is the
    # only credential considered, and a ticket that fails to redeem is rejected outright
    # rather than falling back to the Authorization header. Falling through would mask a
    # bad or replayed ticket whenever the caller happened to also carry a valid header, so
    # a replayed ticket would look accepted and the single-use guarantee would be untestable.
    if ticket is not None:
        return _redeem_websocket_ticket(ticket=ticket)
    return _read_access_token_from_authorization_header(websocket=websocket)


def _redeem_websocket_ticket(ticket: str) -> str:
    try:
        access_token = _websocket_tickets_service.redeem_ticket(ticket=ticket)
    except InvalidWebsocketTicketError:
        # Unknown, expired and already-redeemed tickets are indistinguishable by design in
        # the tickets service, and they stay indistinguishable here: the reason reaches
        # neither the close code nor the log line, and the ticket value is never logged.
        _websocket_logger.debug(
            "Failed to authorize the WebSocket connection request. The ticket provided "
            "in the query string could not be redeemed.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from None

    _websocket_logger.debug(
        "Received WebSocket connection request with a redeemed ticket.",
    )
    return access_token


# The header path is carried over unchanged from the events API endpoint: the REPL client
# authenticates this way and keeps doing so.
def _read_access_token_from_authorization_header(websocket: WebSocket) -> str:
    try:
        # If the Authorization header is not present, KeyError is thrown. The header is in
        # lowercase within the headers dictionary of the websocket object.
        authorization_header = websocket.headers["authorization"]
        if not authorization_header.startswith("Bearer "):
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        # Format of the Authorization header is: Bearer <value>
        encoded_json_web_token = authorization_header[7:]
        decoded_json_web_token = jwt.decode(
            jwt=encoded_json_web_token,
            key=JSON_WEB_TOKEN_SECRET_KEY,
            algorithms=JSON_WEB_TOKEN_ALGORITHMS,
        )
        access_token = decoded_json_web_token["sub"]
    # `KeyError`: Authorization header is not present (or the token carries no `sub`)
    # `IndexError`: Authorization header is empty
    except KeyError, IndexError:
        _websocket_logger.debug(
            "Failed to authorize the WebSocket connection request. The Authorization "
            "header was not provided.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from None
    except jwt.exceptions.InvalidTokenError:
        _websocket_logger.debug(
            "Failed to authorize the WebSocket connection request. The value provided "
            "for the Authorization header was not a validly formatted JSON Web Token.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from None

    _websocket_logger.debug(
        "Received WebSocket connection request with an access value in the "
        "Authorization header.",
    )
    return access_token
