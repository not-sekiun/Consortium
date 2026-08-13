"""Unit tests for the client's websockets events API, covering how it authenticates.

The handshake is authenticated with a single use ticket, so what these tests are really
pinning down is that a ticket is minted per connection attempt and never reused: a stale
ticket presents as an intermittent server side rejection rather than as the client fault
it is.
"""

import urllib.parse

import pytest
from aiohttp import ClientConnectionError
from websockets.datastructures import Headers
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidStatus
from websockets.frames import Close
from websockets.http11 import Response

import consortium.client.client_websockets_events_api as websockets_events_api_module
from consortium.client.client_websockets_events_api import WebsocketsEventsAPI
from consortium.client.exceptions.rest_api_exceptions import RestAPIOperationError
from consortium.client.exceptions.websockets_api_exceptions import (
    WebsocketsAPIFailedToConnectError,
    WebsocketsAPIFailedToObtainTicketError,
    WebsocketsAPITicketRejectedError,
)

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


class _FakeRestAPI:
    # Stands in for the client's REST API. Every call hands back a ticket that has never
    # been handed out before, so a reused one is trivially visible in what the handshake
    # was driven with.
    def __init__(self, error_to_raise: Exception | None = None, response=None):
        self.issued_tickets: list[str] = []
        self._error_to_raise = error_to_raise
        self._response = response

    async def issue_websocket_ticket(self):
        if self._error_to_raise is not None:
            raise self._error_to_raise
        if self._response is not None:
            return self._response

        ticket = f"ticket-{len(self.issued_tickets) + 1}"
        self.issued_tickets.append(ticket)
        return {"ticket": ticket, "time_to_live_seconds": 30}


class _FakeWebsocket:
    async def close(self) -> None:
        return None


class _FakeConnect:
    # Replaces `websockets.connect`, recording every URL a handshake was attempted with.
    def __init__(self, error_to_raise: Exception | None = None):
        self.urls: list[str] = []
        self._error_to_raise = error_to_raise

    async def __call__(self, url: str, **_kwargs):
        self.urls.append(url)
        if self._error_to_raise is not None:
            raise self._error_to_raise
        return _FakeWebsocket()


@pytest.fixture
def fake_connect(monkeypatch):
    def _install(error_to_raise: Exception | None = None) -> _FakeConnect:
        connect = _FakeConnect(error_to_raise=error_to_raise)
        monkeypatch.setattr(
            websockets_events_api_module.websockets,
            "connect",
            connect,
        )
        return connect

    return _install


def _ticket_in(url: str) -> str:
    query_string = urllib.parse.urlparse(url).query
    return urllib.parse.parse_qs(query_string, keep_blank_values=True)["ticket"][0]


async def test_connect_authenticates_the_handshake_with_a_ticket(fake_connect):
    connect = fake_connect()
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)

    rest_api = _FakeRestAPI()
    await events_api.connect(rest_api=rest_api)

    assert events_api.connected
    assert rest_api.issued_tickets == ["ticket-1"]
    assert _ticket_in(connect.urls[0]) == "ticket-1"


async def test_reconnecting_mints_and_uses_a_brand_new_ticket(fake_connect):
    """A second connection must never present the ticket the first one spent.

    This is the automatable half of the "restart the server and reconnect" check: a ticket
    is single use, so a reconnect that reused one would be refused by the server every time
    while looking, from the client, like a server that intermittently rejects good
    credentials.
    """
    connect = fake_connect()
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)
    rest_api = _FakeRestAPI()

    await events_api.connect(rest_api=rest_api)
    await events_api.disconnect()
    await events_api.connect(rest_api=rest_api)

    # Two connection attempts, two issuances, and the second handshake carried the second
    # ticket rather than the first one over again.
    assert len(rest_api.issued_tickets) == 2
    first_ticket, second_ticket = (_ticket_in(url) for url in connect.urls)
    assert first_ticket != second_ticket
    assert [first_ticket, second_ticket] == rest_api.issued_tickets


async def test_a_ticket_is_never_retained_on_the_instance(fake_connect):
    # The structural half of the guarantee above: nothing holds a spent ticket, so no
    # future code path can find one to reuse.
    fake_connect()
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)
    rest_api = _FakeRestAPI()

    await events_api.connect(rest_api=rest_api)

    issued_ticket = rest_api.issued_tickets[0]
    assert all(value != issued_ticket for value in vars(events_api).values())


async def test_a_rest_api_error_while_obtaining_a_ticket_is_typed(fake_connect):
    connect = fake_connect()
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)
    rest_api = _FakeRestAPI(
        error_to_raise=RestAPIOperationError(
            status_code=503,
            code="SERVICE_UNAVAILABLE_ERROR",
            message="Too many outstanding tickets.",
            detail=None,
        ),
    )

    with pytest.raises(WebsocketsAPIFailedToObtainTicketError) as raised:
        await events_api.connect(rest_api=rest_api)

    # The underlying reason has to reach the operator: without it the message says only
    # that a ticket could not be had, and never why.
    assert "Too many outstanding tickets." in str(raised.value)
    # No handshake may be attempted without a ticket to attempt it with.
    assert connect.urls == []
    assert not events_api.connected


async def test_an_unreachable_server_while_obtaining_a_ticket_is_typed(fake_connect):
    # The REST call failing at the transport level is exactly the case a reconnect after a
    # server restart runs into, and it raises out of aiohttp rather than as one of the
    # client's own REST API errors.
    fake_connect()
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)
    rest_api = _FakeRestAPI(error_to_raise=ClientConnectionError("connection refused"))

    with pytest.raises(WebsocketsAPIFailedToObtainTicketError):
        await events_api.connect(rest_api=rest_api)

    assert not events_api.connected


async def test_a_response_carrying_no_ticket_is_typed(fake_connect):
    fake_connect()
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)
    rest_api = _FakeRestAPI(response={"not_a_ticket": "surprise"})

    with pytest.raises(WebsocketsAPIFailedToObtainTicketError):
        await events_api.connect(rest_api=rest_api)

    assert not events_api.connected


async def test_a_handshake_rejected_with_an_http_error_reports_the_ticket_was_refused(
    fake_connect,
):
    # How a refused ticket actually arrives: the server rejects the handshake before
    # accepting it, which its ASGI stack turns into an HTTP 403 on the handshake response.
    fake_connect(
        error_to_raise=InvalidStatus(Response(403, "Forbidden", Headers())),
    )
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)

    with pytest.raises(WebsocketsAPITicketRejectedError):
        await events_api.connect(rest_api=_FakeRestAPI())


async def test_a_handshake_closed_with_a_policy_violation_reports_the_same(
    fake_connect,
):
    fake_connect(
        error_to_raise=ConnectionClosed(Close(1008, "policy violation"), None, None),
    )
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)

    with pytest.raises(WebsocketsAPITicketRejectedError):
        await events_api.connect(rest_api=_FakeRestAPI())


async def test_a_handshake_that_fails_for_any_other_reason_is_not_blamed_on_the_ticket(
    fake_connect,
):
    # A server that is not a Consortium server at all, or one that is not there: the
    # generic failure, which must not be reported as a rejected ticket.
    fake_connect(error_to_raise=InvalidHandshake("not a websocket server"))
    events_api = WebsocketsEventsAPI(remote_host="127.0.0.1", remote_port=9999)

    with pytest.raises(WebsocketsAPIFailedToConnectError):
        await events_api.connect(rest_api=_FakeRestAPI())
