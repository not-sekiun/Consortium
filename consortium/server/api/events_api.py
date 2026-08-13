from fastapi import (
    APIRouter,
    WebSocket,
)
from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import authenticate_websocket_connection

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
    # `get_current_user` dependency uses to obtain the JWT value from the Authorization
    # header is not available in the websocket endpoint. Authentication and authorization
    # for the handshake therefore live in `authenticate_websocket_connection`, which is
    # shared by every websocket route and redeems the handshake's single credential (a
    # ticket in the query string, the only place a browser can put one) into one user
    # lookup and one permission check.
    # TODO: The websocket credential path is handled by that one helper, but the helper
    #  itself is still separate from the REST API's dependencies and from the
    #  authentication middleware. Unify all three so that authorization and authentication
    #  are decided in a single place across the REST API, middleware and websocket
    #  endpoints.
    user = authenticate_websocket_connection(
        websocket=websocket,
        user_permission=UserPermissions.USE_EVENTS_WEBSOCKET,
    )
    _logger.info(
        f"{user} made a WebSocket connection to the events API.",
    )

    await websocket.accept()

    await _events_websocket_service.run_connection(websocket=websocket)
