from typing import Annotated

from fastapi import APIRouter, Depends, Request
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    ServiceUnavailableError,
)
from consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions import (
    TooManyOutstandingWebsocketTicketsError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.models.websocket_ticket_models import WebsocketTicketModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user
from consortium.server.services.websocket_tickets_service import (
    TICKET_TIME_TO_LIVE_SECONDS,
)

# This router carries its own prefix rather than living under the events API router
# (/api/ws/events): ticket issuance is a plain HTTP concern shared by every websocket
# endpoint, not part of the events socket itself. Both sit under /api/ws/ because they are
# websocket concerns.
router = APIRouter(
    prefix="/api/ws/ticket",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Websocket Tickets"],
)
limiter = Limiter(key_func=get_remote_address)

_websocket_tickets_service = server_singletons.websocket_tickets_service

_logger = logger.bind(
    logger_name="Websocket Tickets API",
    logger_type=LoggerType.REST_API_LOGGER,
)

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
    "",
    responses={
        200: {"model": WebsocketTicketModel},
        503: {"model": _ticket_store_full_error.to_pydantic_model()},
    },
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
    # The ticket is bound to the caller's own access token, read off the `User` that the
    # authentication dependency resolved. Note that "access token" here means the JSON Web
    # Token's `sub` claim (`json_web_token.subject`), which is what
    # `users_service.get_user_by_access_token` matches on, NOT the encoded token string
    # that `json_web_token.access_token` holds. The websocket handshake path redeems the
    # ticket and feeds the result straight into that lookup, so binding the encoded string
    # instead would produce a ticket that redeems to a value resolving to no user at all.
    try:
        ticket = _websocket_tickets_service.issue_ticket(
            access_token=str(user.json_web_token.subject),
        )
    except TooManyOutstandingWebsocketTicketsError:
        # The cap is a server wide resource limit that a caller can do nothing about
        # except retry, so it is reported as a 503 rather than as a client error. The
        # response deliberately does not echo the cap or the current occupancy back.
        _logger.warning(
            "Failed to issue a websocket ticket to {}. The outstanding ticket cap has "
            "been reached.",
            user,
        )
        raise ServiceUnavailableError(message=_TICKET_STORE_FULL_MESSAGE) from None

    _logger.debug("Issued a websocket ticket to {}.", user)

    return WebsocketTicketModel(
        ticket=ticket,
        time_to_live_seconds=TICKET_TIME_TO_LIVE_SECONDS,
    )
