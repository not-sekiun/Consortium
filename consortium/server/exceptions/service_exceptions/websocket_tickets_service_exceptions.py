"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`WebsocketTicketsServiceError`][consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions.WebsocketTicketsServiceError]
        - [`InvalidWebsocketTicketError`][consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions.InvalidWebsocketTicketError]
        - [`TooManyOutstandingWebsocketTicketsError`][consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions.TooManyOutstandingWebsocketTicketsError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class WebsocketTicketsServiceError(BaseServiceError):
    """Base exception for all errors that occur within the websocket tickets service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "WEBSOCKET_TICKETS_SERVICE_ERROR"


class InvalidWebsocketTicketError(WebsocketTicketsServiceError):
    """Raised when a ticket presented for redemption cannot be honoured.

    This single error deliberately covers all three redemption failures alike: a ticket
    that was never issued, a ticket that has expired, and a ticket that was already
    redeemed. They are reported with the identical type, code and message, and the
    ticket value is never included in the message or detail. Distinguishing them would
    turn redemption into an oracle: an attacker could probe whether a given ticket value
    ever existed, or whether it is merely spent versus fabricated. Keeping the three
    indistinguishable denies that signal.
    """

    code = "INVALID_WEBSOCKET_TICKET_ERROR"

    def __init__(self):
        super().__init__(
            message=(
                "Failed to redeem the provided websocket ticket. The ticket is not "
                "valid. Request a new ticket and present it on the websocket handshake "
                "promptly, as tickets are single use and short lived."
            ),
        )


class TooManyOutstandingWebsocketTicketsError(WebsocketTicketsServiceError):
    """Raised when a ticket cannot be issued because the number of outstanding,
    unredeemed tickets is already at the configured cap.

    The cap bounds the memory the in-memory ticket store can occupy. Reaching it
    indicates either an unusual burst of handshakes or tickets being issued but not
    redeemed. Retry after outstanding tickets expire or are redeemed.
    """

    code = "TOO_MANY_OUTSTANDING_WEBSOCKET_TICKETS_ERROR"

    def __init__(self, max_outstanding_tickets: int):
        super().__init__(
            message=(
                f"Failed to issue a websocket ticket. The number of outstanding "
                f"websocket tickets is already at the cap of {max_outstanding_tickets}. "
                f"Retry once outstanding tickets expire or are redeemed."
            ),
            detail={
                "max_outstanding_tickets": max_outstanding_tickets,
            },
        )
