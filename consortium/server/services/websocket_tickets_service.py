import secrets
import time

from loguru import logger

from consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions import (
    InvalidWebsocketTicketError,
    TooManyOutstandingWebsocketTicketsError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import log_and_propagate_error_on_service_method

# How long an issued ticket remains redeemable, in seconds. A ticket is a session handoff
# credential: an already-authenticated caller trades its JWT for a ticket, then presents
# the ticket on a websocket handshake (browsers cannot set request headers on a handshake,
# so the token cannot travel there). The window only has to cover the round trip from
# issuing the ticket to opening the socket, so it is deliberately tight: a shorter life
# shrinks the window in which a leaked ticket (e.g. from a proxy or access log) is usable.
# Retune upward only if legitimate handshakes are observed racing past this bound.
TICKET_TIME_TO_LIVE_SECONDS = 30

# Upper bound on the number of outstanding, unredeemed tickets held at once. Tickets live
# only in memory, so this caps that memory: each entry is a short random string plus a
# token and a float, on the order of a few hundred bytes, so 10,000 entries is well under a
# few megabytes worst case. It is set far above any plausible count of humans mid-handshake
# at one instant (tickets are reaped on expiry and removed on redemption, so the steady
# state is tiny) yet low enough that a caller spamming issue calls cannot exhaust memory.
# Retune from expected concurrent handshake volume, not from a single client's behaviour.
MAX_OUTSTANDING_TICKETS = 10_000


# Short-lived, single-use handshake credentials ("tickets") for authenticating websocket
# connections. An already-authenticated caller trades its access token for an opaque
# ticket via `issue_ticket`, and the websocket handshake path exchanges that ticket back
# for the access token via `redeem_ticket`. Single use is enforced by removal from the
# store on redemption, not by a flag: see `redeem_ticket`.
class WebsocketTicketsService:
    def __init__(self):
        # Maps ticket -> (access_token, expiry_monotonic). The expiry is a
        # `time.monotonic()` deadline, not a wall-clock time, so a system clock change
        # cannot extend or shorten a ticket's life.
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
    def issue_ticket(self, access_token: str) -> str:
        """Issues a fresh single-use ticket bound to the provided access token.

        The returned ticket is opaque and randomly generated: it encodes nothing about
        the access token or the user, and cannot be derived from either. Present it on a
        websocket handshake, where it can be exchanged for the access token exactly once
        via `redeem_ticket` before it expires.

        Args:
            access_token: The access token the caller has already authenticated with,
                which the issued ticket will resolve back to on redemption.

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

        ticket = secrets.token_urlsafe(32)
        expiry = time.monotonic() + TICKET_TIME_TO_LIVE_SECONDS
        self._tickets[ticket] = (access_token, expiry)
        self._logger.debug("Issued a websocket ticket")
        return ticket

    @log_and_propagate_error_on_service_method
    def redeem_ticket(self, ticket: str) -> str:
        """Redeems a ticket, returning the access token it was issued for.

        A ticket may be redeemed at most once. Redemption removes the ticket from the
        store, so a second redemption of the same ticket fails.

        This method deliberately raises the same `InvalidWebsocketTicketError` for a
        ticket that was never issued, one that has expired, and one that was already
        redeemed. The three are indistinguishable by design (see the exception's
        docstring): reporting them differently would let a caller probe the store as an
        oracle.

        Args:
            ticket: The ticket string presented on the websocket handshake.

        Returns:
            The access token the ticket was issued for.

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
        # This indistinguishability is deliberate: do not split it into separate error
        # types, codes or messages, and do not echo the ticket value back. Doing so would
        # turn redemption into an oracle for whether a ticket ever existed or is merely
        # spent versus fabricated.
        if entry is None:
            raise InvalidWebsocketTicketError()

        access_token, expiry = entry
        if time.monotonic() >= expiry:
            # Expired: it was popped above, so it is already gone from the store. Report
            # it as invalid, identically to the unknown case.
            raise InvalidWebsocketTicketError()

        self._logger.debug("Redeemed a websocket ticket")
        return access_token

    def _reap_expired_tickets(self) -> None:
        # Drop every entry whose monotonic deadline has passed. Materialise the expired
        # keys first, then delete, so the dict is not mutated while being iterated.
        now = time.monotonic()
        expired = [
            ticket
            for ticket, (_token, expiry) in self._tickets.items()
            if now >= expiry
        ]
        for ticket in expired:
            self._tickets.pop(ticket, None)
