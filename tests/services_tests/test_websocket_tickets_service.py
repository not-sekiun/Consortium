import asyncio
import uuid

import pytest

from consortium.server.exceptions.service_exceptions.websocket_tickets_service_exceptions import (
    InvalidWebsocketTicketError,
    TooManyOutstandingWebsocketTicketsError,
)
from consortium.server.services import websocket_tickets_service as service_module
from consortium.server.services.websocket_tickets_service import (
    WebsocketTicketsService,
)

# Match the async test convention used elsewhere in tests/services_tests: the anyio
# backend is pinned to asyncio by the session-scoped fixture in conftest.py.
pytestmark = pytest.mark.anyio


class _FakeClock:
    # A controllable stand-in for time.monotonic so expiry can be tested by advancing time
    # explicitly, never by sleeping. Monotonic semantics: the value only moves forward when
    # a test advances it.
    def __init__(self):
        self._now = 1000.0

    def monotonic(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake_clock = _FakeClock()
    # Patch the monotonic function the service actually reads (it calls
    # `time.monotonic()` against the `time` module imported in its own namespace).
    monkeypatch.setattr(service_module.time, "monotonic", fake_clock.monotonic)
    return fake_clock


@pytest.fixture
def service():
    return WebsocketTicketsService()


def test_issued_ticket_redeems_once_returning_exact_user_id(service, clock):
    user_id = str(uuid.uuid4())
    ticket = service.issue_ticket(user_id=user_id)

    redeemed = service.redeem_ticket(ticket=ticket)

    assert redeemed == user_id


def test_uuid_user_id_is_normalized_to_a_string_on_redemption(service, clock):
    # The users service keys its registry on the string form of a user ID, so a ticket
    # issued with a UUID object must still redeem to something that lookup can match.
    user_id = uuid.uuid4()
    ticket = service.issue_ticket(user_id=user_id)

    redeemed = service.redeem_ticket(ticket=ticket)

    assert redeemed == str(user_id)
    assert isinstance(redeemed, str)


def test_second_redemption_fails(service, clock):
    ticket = service.issue_ticket(user_id=str(uuid.uuid4()))

    service.redeem_ticket(ticket=ticket)

    with pytest.raises(InvalidWebsocketTicketError):
        service.redeem_ticket(ticket=ticket)


def test_expired_ticket_fails_and_is_reaped_from_store(service, clock):
    # Issue a ticket, let it expire, then issue a second ticket. The second issue triggers
    # the lazy reap, which must remove the expired first ticket from the internal store.
    expired_ticket = service.issue_ticket(user_id=str(uuid.uuid4()))
    assert expired_ticket in service._tickets

    clock.advance(service_module.TICKET_TIME_TO_LIVE_SECONDS + 1)

    # Issuing sweeps expired entries before inserting, so the expired ticket must be gone.
    service.issue_ticket(user_id=str(uuid.uuid4()))

    assert expired_ticket not in service._tickets
    # And redeeming the expired ticket fails.
    with pytest.raises(InvalidWebsocketTicketError):
        service.redeem_ticket(ticket=expired_ticket)


def test_unknown_expired_and_redeemed_are_indistinguishable(service, clock):
    # The security property: a caller must not be able to tell an unknown ticket apart
    # from an expired one apart from an already-redeemed one. All three must raise the
    # identical error type with the identical message, and never echo the ticket value.

    # Unknown: never issued.
    with pytest.raises(InvalidWebsocketTicketError) as unknown_exc_info:
        service.redeem_ticket(ticket="never-issued-ticket-value")

    # Already redeemed.
    redeemed_ticket = service.issue_ticket(user_id=str(uuid.uuid4()))
    service.redeem_ticket(ticket=redeemed_ticket)
    with pytest.raises(InvalidWebsocketTicketError) as redeemed_exc_info:
        service.redeem_ticket(ticket=redeemed_ticket)

    # Expired.
    expired_ticket = service.issue_ticket(user_id=str(uuid.uuid4()))
    clock.advance(service_module.TICKET_TIME_TO_LIVE_SECONDS + 1)
    with pytest.raises(InvalidWebsocketTicketError) as expired_exc_info:
        service.redeem_ticket(ticket=expired_ticket)

    unknown_exc = unknown_exc_info.value
    redeemed_exc = redeemed_exc_info.value
    expired_exc = expired_exc_info.value

    # Identical type across all three.
    assert type(unknown_exc) is type(redeemed_exc) is type(expired_exc)
    assert (
        unknown_exc.code
        == redeemed_exc.code
        == expired_exc.code
        == "INVALID_WEBSOCKET_TICKET_ERROR"
    )
    # Identical message across all three.
    assert unknown_exc.message == redeemed_exc.message == expired_exc.message
    # Detail carries nothing that could distinguish them or leak a ticket value.
    assert unknown_exc.detail == redeemed_exc.detail == expired_exc.detail is None
    # No ticket value is leaked into the message.
    for ticket_value in ("never-issued-ticket-value", redeemed_ticket, expired_ticket):
        assert ticket_value not in unknown_exc.message
        assert ticket_value not in redeemed_exc.message
        assert ticket_value not in expired_exc.message


async def test_concurrent_redemption_succeeds_exactly_once(service, clock):
    # Fan many concurrent redemptions of the same ticket out over asyncio.gather. Exactly
    # one must succeed and the rest must raise InvalidWebsocketTicketError. This holds
    # because redeem_ticket is synchronous: the single dict pop cannot be suspended
    # mid-way, so only one coroutine can observe the ticket present.
    user_id = str(uuid.uuid4())
    ticket = service.issue_ticket(user_id=user_id)

    async def attempt():
        return service.redeem_ticket(ticket=ticket)

    results = await asyncio.gather(
        *[attempt() for _ in range(64)], return_exceptions=True
    )

    successes = [result for result in results if result == user_id]
    failures = [
        result for result in results if isinstance(result, InvalidWebsocketTicketError)
    ]

    assert len(successes) == 1
    assert len(failures) == len(results) - 1


def test_issuing_beyond_cap_raises(service, clock, monkeypatch):
    # Shrink the cap so the test does not have to issue ten thousand tickets. The service
    # reads MAX_OUTSTANDING_TICKETS from its module namespace at call time.
    monkeypatch.setattr(service_module, "MAX_OUTSTANDING_TICKETS", 3)

    for _ in range(3):
        service.issue_ticket(user_id=str(uuid.uuid4()))

    with pytest.raises(TooManyOutstandingWebsocketTicketsError):
        service.issue_ticket(user_id=str(uuid.uuid4()))


def test_two_tickets_for_same_user_are_different_values(service, clock):
    # Tickets must be random, not derived from the user ID: issuing twice for the same
    # session yields two distinct opaque values.
    user_id = str(uuid.uuid4())
    first_ticket = service.issue_ticket(user_id=user_id)
    second_ticket = service.issue_ticket(user_id=user_id)

    assert first_ticket != second_ticket
    # And neither ticket embeds the user ID it was issued for.
    assert user_id not in first_ticket
    assert user_id not in second_ticket
