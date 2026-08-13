import jwt
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketException,
    status,
)
from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
)
from consortium.server.exceptions.service_exceptions.users_service_exceptions import (
    UserAccessTokenNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_jwt_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_SECRET_KEY,
)

router = APIRouter(
    prefix="/api/ws/events",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Events"],
)

_users_service = server_singletons.users_service
_authorization_service = server_singletons.authorization_service
_events_websocket_service = server_singletons.events_websocket_service

_logger = logger.bind(
    logger_name="Websocket Events API",
    logger_type=LoggerType.WEBSOCKET_EVENTS_API_LOGGER,
)


@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
):
    # We cannot use the user dependency here because the Request object which the
    # `get_current_use` dependency uses to obtain the JWT value from the Authorization
    # header is not available in the websocket endpoint. Instead, we access headers
    # from the Websocket object. Hence, we implement authorization and authentication
    # manually here.
    # TODO: Fix this manual work around so that we can unify all the authorization and
    #  authentication checks in one place across the REST API, middleware and websocket
    #  endpoints.
    try:
        auth_header = websocket.headers["authorization"]
        if not auth_header.startswith("Bearer "):
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        encoded_json_web_token = auth_header[7:]
        decoded_json_web_token = jwt.decode(
            jwt=encoded_json_web_token,
            key=JSON_WEB_TOKEN_SECRET_KEY,
            algorithms=JSON_WEB_TOKEN_ALGORITHMS,
        )
        access_token = decoded_json_web_token["sub"]
        _logger.debug(
            "Received WebSocket connection request with an access value in the "
            "Authorization header.",
        )
        user = _users_service.get_user_by_access_token(
            access_token=access_token,
        )
        _logger.info(
            f"{user} made a WebSocket connection to the events API.",
        )
    except KeyError, IndexError:
        _logger.debug(
            "Failed to authorize the WebSocket connection request. The Authorization "
            "header was not provided.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from None
    except jwt.exceptions.InvalidTokenError:
        _logger.debug(
            "Failed to authorize the WebSocket connection request. The value provided "
            "for the Authorization header was not a validly formatted JSON Web Token.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from None
    except UserAccessTokenNotFoundError:
        _logger.debug(
            "Failed to authorize the WebSocket connection request. The access "
            "value provided in the JSON Web Token was not found.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from None

    if not _authorization_service.has_permission(
        user.role, UserPermissions.USE_EVENTS_WEBSOCKET
    ):
        _logger.debug(
            f"Rejected WebSocket connection attempt because the user '{user}' had "
            f"insufficient permissions to interact with the events API.",
        )
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    await websocket.accept()

    await _events_websocket_service.run_connection(websocket=websocket)
