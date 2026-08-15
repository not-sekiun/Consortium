from typing import Annotated

from fastapi import APIRouter, Depends, Request, WebSocket
from slowapi import Limiter
from slowapi.util import get_remote_address

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    ServiceUnavailableError,
    TooManyRequestsError,
)
from consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions import (
    TooManyOutstandingWebsocketTicketsError,
)
from consortium.server.models.websocket_ticket_models import WebsocketTicketModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import (
    AuthorizeUserRequest,
    authenticate_websocket_connection,
    get_current_user,
)
from consortium.server.services.websocket_tickets_service import (
    TICKET_TIME_TO_LIVE_SECONDS,
)

router = APIRouter(
    prefix="/api/ws",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
limiter = Limiter(key_func=get_remote_address)

_events_websocket_service = server_singletons.events_websocket_service
_websocket_tickets_service = server_singletons.websocket_tickets_service

# No logger is bound in this module by design. Routes here are a thin translation layer
# between HTTP and the services, so everything worth recording (a ticket issued, a
# redemption, a connection served, a service error) is logged by the service that performs
# it. Logging here as well would double every line under two logger names.

_TICKET_STORE_FULL_MESSAGE = (
    "A websocket ticket could not be issued because the server is holding too many "
    "outstanding tickets. Please try again in a moment."
)
_ticket_store_full_error = ServiceUnavailableError(
    message=_TICKET_STORE_FULL_MESSAGE,
)


# The rate limit here is not about CPU: issuing a ticket is one random token and one dict
# insert. It is about the store's `MAX_OUTSTANDING_TICKETS` cap, which bounds the whole
# server rather than any one caller. Without a limit a single authenticated caller could
# spam issuance, fill that cap and starve every other user of tickets, so the limit is what
# keeps one caller from denying the endpoint to everybody else. 20 per minute leaves a
# caller holding at most a few tens of unredeemed tickets at once (tickets die after
# `TICKET_TIME_TO_LIVE_SECONDS`), which is orders of magnitude below the cap, while staying
# far above legitimate demand: a client needs exactly one ticket per handshake, so only page
# reloads and reconnect attempts spend from the budget.
@router.post(
    "/ticket",
    responses={
        200: {"model": WebsocketTicketModel},
        429: {"model": TooManyRequestsError().to_pydantic_model()},
        503: {"model": _ticket_store_full_error.to_pydantic_model()},
    },
    tags=["Websocket Tickets"],
)
@limiter.limit("20/minute")
async def issue_websocket_ticket(
    request: Request,  # Declaring request here is necessary for the rate limiter
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.USE_EVENTS_WEBSOCKET)),
    ],
) -> WebsocketTicketModel:
    """Issues a short-lived, single-use ticket for authenticating a websocket handshake.

    A browser cannot set request headers on a websocket handshake, so it cannot present
    its JSON Web Token there the way it does on every other request. Instead it calls this
    endpoint over ordinary HTTP (where the token travels in the Authorization header as
    usual) and receives an opaque ticket to present on the handshake in place of the token.

    The ticket is always minted for the calling user's own session. The endpoint takes no
    request body and no user identifier, so there is no way to request a ticket bound to
    another user's session.

    Requires the `USE_EVENTS_WEBSOCKET` permission: the same permission the websocket
    endpoint itself checks, so obtaining a ticket can never be a way around that check.

    Returns:
        The issued ticket along with the number of seconds it remains redeemable for.
    """
    # The ticket is bound to the ID of the caller's own session, read off the `User` that
    # the authentication dependency resolved. The handshake path redeems the ticket back
    # into this ID and resolves it through `users_service.get_user_by_user_id`, so the
    # socket ends up serving the very session that asked for the ticket.
    try:
        ticket = _websocket_tickets_service.issue_ticket(user_id=user.user_id)
    except TooManyOutstandingWebsocketTicketsError:
        # The cap is a server wide resource limit that a caller can do nothing about
        # except retry, so it is reported as a 503 rather than as a client error. The
        # response deliberately does not echo the cap or the current occupancy back. The
        # failure itself is already logged by the tickets service.
        raise ServiceUnavailableError(message=_TICKET_STORE_FULL_MESSAGE) from None

    return WebsocketTicketModel(
        ticket=ticket,
        time_to_live_seconds=TICKET_TIME_TO_LIVE_SECONDS,
    )


@router.websocket("/events")
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

    await websocket.accept()

    # `user` is handed on so the service can report the connection: this endpoint does no
    # logging of its own.
    await _events_websocket_service.handle_connection(websocket=websocket, user=user)
