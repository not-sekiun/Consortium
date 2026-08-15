import secrets
import time
import uuid

from loguru import logger

from consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions import (
    InvalidWebsocketTicketError,
    TooManyOutstandingWebsocketTicketsError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)

# How long an issued ticket remains redeemable, in seconds. A ticket is a session handoff
# credential: an already-authenticated caller trades its JWT for a ticket, then presents
# the ticket on a websocket handshake (browsers cannot set request headers on a handshake,
# so the token cannot travel there). The window only has to cover the round trip from
# issuing the ticket to opening the socket, so it is deliberately tight: a shorter life
# shrinks the window in which a leaked ticket (e.g. from a proxy or access log) is usable.
TICKET_TIME_TO_LIVE_SECONDS = 30

# Upper bound on the number of outstanding, unredeemed tickets held at once. Tickets live
# only in memory, so this caps that memory: each entry is a short random string plus a
# token and a float, on the order of a few hundred bytes, so 10,000 entries is well under a
# few megabytes worst case.
MAX_OUTSTANDING_TICKETS = 10_000


# Short-lived, single-use handshake credentials ("tickets") for authenticating websocket
# connections. An already-authenticated caller trades its session for an opaque ticket via
# `issue_ticket`, and the websocket handshake path exchanges that ticket back for the user
# ID of that session via `redeem_ticket`.
class WebsocketTicketsService:
    def __init__(self):
        # Maps ticket -> (user_id, expiry_monotonic). The expiry is a `time.monotonic()`
        # deadline, not a wall-clock time, so a system clock change cannot extend or
        # shorten a ticket's life.
        self._tickets: dict[str, tuple[str, float]] = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self):
        return "Websocket Tickets Service"

    def __repr__(self):
        return "WebsocketTicketsService()"

    @log_and_propagate_error_on_service_method
    def issue_ticket(self, user_id: str | uuid.UUID) -> str:
        """Issues a fresh single-use ticket bound to the provided user session.

        The returned ticket is opaque and randomly generated: it encodes nothing about
        the user, and cannot be derived from the user ID. Present it on a websocket
        handshake, where it can be exchanged for the user ID exactly once via
        `redeem_ticket` before it expires.

        The user ID is stored as given and is never validated against the users service:
        a ticket for a session that has since ended still redeems, and it is the caller's
        job to resolve the returned ID and handle a session that no longer exists.

        Args:
            user_id: The ID of the already-authenticated user session the issued ticket
                will resolve back to on redemption.

        Returns:
            An opaque, single-use ticket string.

        Raises:
            TooManyOutstandingWebsocketTicketsError: If the number of outstanding,
                unredeemed tickets is already at the configured cap after expired tickets
                have been reaped.
        """
        # Reap lazily on the issue path so expired entries never accumulate, and so the
        # cap check below is made against genuinely live tickets rather than dead ones.
        # This is done instead of a background reaper task: a reaper would need a
        # startup/shutdown lifecycle hook that this service does not own.
        self._reap_expired_tickets()

        # Reject rather than evict: the cap is hit only after reaping live tickets, so
        # every remaining entry is a valid outstanding ticket belonging to someone. Silently
        # dropping one to make room would invalidate another caller's in-flight handshake.
        if len(self._tickets) >= MAX_OUTSTANDING_TICKETS:
            raise TooManyOutstandingWebsocketTicketsError(
                max_outstanding_tickets=MAX_OUTSTANDING_TICKETS
            )

        user_id = normalize_uuid(user_id)

        ticket = secrets.token_urlsafe(32)
        expiry = time.monotonic() + TICKET_TIME_TO_LIVE_SECONDS
        self._tickets[ticket] = (user_id, expiry)
        # The user ID is logged but the ticket value never is: the ticket is the secret
        # here, and an issued one is still redeemable for its whole lifetime, so writing it
        # to a log would put a live credential somewhere far longer lived than the ticket.
        self._logger.debug("Issued a websocket ticket to user '{}'", user_id)
        return ticket

    @log_and_propagate_error_on_service_method
    def redeem_ticket(self, ticket: str) -> str:
        """Redeems a ticket, returning the ID of the user session it was issued for.

        A ticket may be redeemed at most once. Redemption removes the ticket from the
        store, so a second redemption of the same ticket fails.

        A successful redemption proves only that the ticket was issued and is unspent. It
        says nothing about whether that session is still logged in, so the returned ID
        must still be resolved against the users service.

        This method deliberately raises the same `InvalidWebsocketTicketError` for a
        ticket that was never issued, one that has expired, and one that was already
        redeemed. The three are indistinguishable by design (see the exception's
        docstring): reporting them differently would let a caller probe the store as an
        oracle.

        Args:
            ticket: The ticket string presented on the websocket handshake.

        Returns:
            The ID of the user session the ticket was issued for.

        Raises:
            InvalidWebsocketTicketError: If the ticket is unknown, expired, or already
                redeemed. These three cases are intentionally not distinguished.
        """
        # This method is a plain `def` and contains no `await` on purpose. Popping the
        # ticket out of the store is what enforces single use, and it is safe against
        # concurrent redemption precisely because this function is synchronous: the event
        # loop cannot suspend it partway through, so two coroutines racing to redeem the
        # same ticket cannot both observe it present. Exactly one pop returns the entry;
        # the other gets the default. A redeemed-flag, or any check-then-act split across
        # an `await`, would reintroduce that race. Do NOT make this async or add an await.
        entry = self._tickets.pop(ticket, None)

        # Unknown, expired and already-redeemed all funnel to one error with one message.
        # Do not split it into separate error types, codes or messages, and do not echo
        # the ticket value back. Doing so would leak information.
        if entry is None:
            raise InvalidWebsocketTicketError()

        user_id, expiry = entry
        if time.monotonic() >= expiry:
            # Expired: it was popped above, so it is already gone from the store. Report
            # it as invalid, identically to the unknown case.
            raise InvalidWebsocketTicketError()

        self._logger.debug("Redeemed a websocket ticket for user '{}'", user_id)
        return user_id

    def _reap_expired_tickets(self) -> None:
        # Drop every entry whose monotonic deadline has passed.
        now = time.monotonic()
        expired = [
            ticket
            for ticket, (_user_id, expiry) in self._tickets.items()
            if now >= expiry
        ]
        for ticket in expired:
            self._tickets.pop(ticket, None)
