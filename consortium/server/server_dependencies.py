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
# endpoint. A handshake carries its credential in exactly one place, a ticket in the query
# string, because that is the only place a browser can put one (it can set neither headers
# nor a body on a handshake). Hence this helper: it redeems the presented ticket into an
# access token, then resolves the user and checks the permission, so every websocket route
# is authenticated and authorized identically.
#
# Raises `WebSocketException` with `WS_1008_POLICY_VIOLATION` on any failure. Every reason
# closes with that same code and nothing distinguishes them to the client: a missing ticket,
# an invalid ticket, an unknown user and an insufficient permission are all reported alike.
# The per-reason detail is written to the debug log instead, so operators can diagnose a
# failed handshake without the code becoming an oracle for callers.
def authenticate_websocket_connection(
    websocket: WebSocket,
    user_permission: UserPermissions,
) -> User:
    access_token = _resolve_websocket_access_token(websocket=websocket)

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
    # A ticket is the only credential a handshake can present. Anything else a caller sends
    # (an Authorization header in particular, which the REPL client used to authenticate
    # with before it moved to tickets) is ignored entirely, so a handshake without a ticket
    # is rejected here rather than falling back to a second credential source. One path
    # means a bad or replayed ticket can never be masked by another credential the caller
    # happened to also carry, and the single-use guarantee stays observable.
    if ticket is None:
        _websocket_logger.debug(
            "Failed to authorize the WebSocket connection request. No ticket was "
            "provided in the query string.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return _redeem_websocket_ticket(ticket=ticket)


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
