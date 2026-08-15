"""Genuinely end-to-end tests for the browser websocket authentication handshake.

Where test_events_api.py starts from pre-authenticated session-client fixtures, every
happy-path test here begins at a cold start: a real POST /api/login for a JWT, POST
/api/ws/ticket to exchange that JWT for a single-use ticket, and a websocket handshake
carrying only ?ticket= and no Authorization header. That is exactly the path a browser
walks, and the distinct value of this module is exercising the whole chain end to end
rather than any single link in isolation.

A ticket in the query string is the only way to authenticate a handshake: the header
path was removed in #48, so there is deliberately no Authorization header anywhere on
the socket side of these tests."""

import httpx
import pytest

import consortium.server.server_singletons as server_singletons
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.services.websocket_tickets_service import (
    TICKET_TIME_TO_LIVE_SECONDS,
)
from tests.api_tests.websocket_helpers import (
    TICKET_PATH,
    outstanding_ticket_count,
    user_id_of,
)

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Cold-start login
# ---------------------------------------------------------------------------


@pytest.fixture
async def cold_login(app):
    """Factory that logs a user in from a cold start and yields (client, jwt).

    Each call creates a brand new httpx client with no ambient credentials, posts real
    form credentials to /api/login, and comes away carrying only the JWT it was issued,
    exactly as a browser would before it has any session. Deliberately does not reuse the
    session client fixtures: the point of this module is that the chain works from
    nothing. Every client produced is closed on teardown.
    """
    clients: list[httpx.AsyncClient] = []

    async def _login(username: str, password: str) -> tuple[httpx.AsyncClient, str]:
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        )
        clients.append(client)
        response = await client.post(
            "/api/login",
            data={"username": username, "password": password},
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        return client, token

    yield _login

    for client in clients:
        await client.aclose()


# ---------------------------------------------------------------------------
# Happy path: the whole chain, cold start to event delivery
# ---------------------------------------------------------------------------


async def test_full_browser_handshake_from_login_to_event_delivery(ws, cold_login):
    """The whole chain from a cold start: login -> ticket -> ticketed handshake -> event.

    Nothing here reuses a pre-authenticated fixture. A fresh client logs in for a JWT,
    exchanges it for a ticket over POST /api/ws/ticket, and opens the socket with only
    ?ticket= and no Authorization header. The socket then has to be usable, not merely
    accepted, so it subscribes and receives a real server-triggered event over it.
    """
    client, _token = await cold_login("admin", "admin")

    # Exchange the JWT for a single-use ticket the way a browser must: an ordinary
    # authenticated HTTP call whose Authorization header is the last place the token
    # travels before the socket, which never sees a header at all.
    ticket_response = await client.post(TICKET_PATH)
    assert ticket_response.status_code == 200, ticket_response.text
    ticket = ticket_response.json()["ticket"]

    accepted = await ws.open(headers={}, query_params={"ticket": ticket})
    assert accepted

    event_type = EventType.LISTENER_CREATED
    await ws.send_json({"action": "subscribe", "events": [str(event_type)]})
    subscribe_response = await ws.receive_json()
    assert subscribe_response["success"] is True

    await server_singletons.events_service.trigger_event(
        event_type=event_type,
        message="cold start handshake",
        data={"key": "value"},
    )

    event_message = await ws.receive_json()
    assert event_message["type"] == "event"
    assert event_message["event_type"] == str(event_type)
    assert event_message["message"] == "cold start handshake"
    assert event_message["data"] == {"key": "value"}


# ---------------------------------------------------------------------------
# Negative case: a redeemed ticket cannot be reused
# ---------------------------------------------------------------------------


async def test_a_redeemed_ticket_cannot_be_used_a_second_time(ws_factory, cold_login):
    """Single use is enforced at the handshake: the second use of a ticket is refused.

    The first connection is asserted accepted (the positive guard), so the rejection of
    the second can only be the replay, not a ticket that was never valid to begin with.
    """
    client, _token = await cold_login("admin", "admin")
    ticket = (await client.post(TICKET_PATH)).json()["ticket"]

    first_connection = ws_factory()
    assert await first_connection.open(query_params={"ticket": ticket})

    replayed_connection = ws_factory()
    accepted = await replayed_connection.open(query_params={"ticket": ticket})

    assert not accepted
    assert replayed_connection.close_code == 1008


# ---------------------------------------------------------------------------
# Negative case: an expired ticket is rejected (clock, never sleep)
# ---------------------------------------------------------------------------


async def test_an_expired_ticket_is_rejected(ws, cold_login, ticket_clock):
    """A ticket presented after its TTL has elapsed is refused.

    Expiry is driven by the monkeypatched clock, never by sleeping. The ticket is minted
    against that same clock (issuance goes through the service, which reads it), so
    advancing past the TTL is what makes it stale.
    """
    client, _token = await cold_login("admin", "admin")
    ticket = (await client.post(TICKET_PATH)).json()["ticket"]

    ticket_clock.advance(TICKET_TIME_TO_LIVE_SECONDS + 1)

    accepted = await ws.open(query_params={"ticket": ticket})

    assert not accepted
    assert ws.close_code == 1008


async def test_a_ticket_just_inside_its_lifetime_still_connects(
    ws, cold_login, ticket_clock
):
    # Guards the expiry test against passing for the wrong reason: the same flow, with the
    # clock moved to just short of the deadline, is still accepted, so the rejection above
    # can only have come from the ticket having expired.
    client, _token = await cold_login("admin", "admin")
    ticket = (await client.post(TICKET_PATH)).json()["ticket"]

    ticket_clock.advance(TICKET_TIME_TO_LIVE_SECONDS - 1)

    assert await ws.open(query_params={"ticket": ticket})


# ---------------------------------------------------------------------------
# Negative case: no credentials at all
# ---------------------------------------------------------------------------


async def test_a_handshake_with_no_credentials_at_all_is_rejected(
    ws_factory, cold_login
):
    """A handshake presenting neither a ticket nor any header is refused.

    Paired with a positive guard: the very same endpoint accepts a handshake that does
    carry a valid ticket, so the rejection is attributable to the absent credential and
    not to a socket that refuses everyone.
    """
    no_credentials_connection = ws_factory()
    accepted = await no_credentials_connection.open()

    assert not accepted
    assert no_credentials_connection.close_code == 1008

    client, _token = await cold_login("admin", "admin")
    ticket = (await client.post(TICKET_PATH)).json()["ticket"]
    guard_connection = ws_factory()
    assert await guard_connection.open(query_params={"ticket": ticket})


# ---------------------------------------------------------------------------
# The identity-binding case: a ticket cannot be redeemed to act as another user
#
# This is the failure mode that turns a ticket system into an authentication bypass, and
# it is invisible in a happy-path test because the socket never announces whose session
# it is. It is attacked here from two directions: through the socket (authorization
# follows the ticket's own user) and directly at the service (a redeemed ticket resolves
# to exactly one user).
# ---------------------------------------------------------------------------


async def test_authorization_follows_the_tickets_own_user_not_the_presenter(
    ws_factory,
    cold_login,
    spectator_role_without_events_websocket_permission,
):
    """Authorization on the handshake follows the identity bound into the ticket.

    A ticket is minted for the spectator, whose role has had USE_EVENTS_WEBSOCKET
    stripped, and presented on a handshake. The handshake is refused. The only way the
    server can know to refuse is by resolving the identity the ticket carries and applying
    THAT user's permissions: nothing about the presenter, the transport, or any ambient
    session says who the spectator is, and no Authorization header is sent. The ticket is
    minted straight from the service rather than over POST /api/ws/ticket, because that
    endpoint requires the very permission the fixture strips.

    Paired, under the exact same stripped-permission conditions, with a ticket carrying a
    PERMITTED identity (admin, whose role keeps the permission) being accepted on the same
    handshake path. So the rejection is attributable to the identity the ticket carries,
    not to the socket being down for everyone.

    What this proves: the handshake authorizes against the identity bound into the ticket,
    not the presenter or an ambient session. What it does NOT prove on its own is that the
    resolved identity is that exact spectator rather than merely 'some user who happens to
    lack the permission'. The direct-resolution tests below close that gap by pinning a
    redeemed ticket to one specific user and to nobody else.
    """
    spectator_client, _token = await cold_login("spectator", "spectator")
    outstanding_tickets_before = outstanding_ticket_count()

    stripped_user_ticket = server_singletons.websocket_tickets_service.issue_ticket(
        user_id=user_id_of(spectator_client),
    )
    stripped_connection = ws_factory()
    accepted = await stripped_connection.open(
        query_params={"ticket": stripped_user_ticket}
    )

    assert not accepted
    assert stripped_connection.close_code == 1008

    # Positive guard: a ticket for a permitted identity, under the same stripped-permission
    # conditions, is accepted on the same handshake path.
    admin_client, _admin_token = await cold_login("admin", "admin")
    permitted_user_ticket = server_singletons.websocket_tickets_service.issue_ticket(
        user_id=user_id_of(admin_client),
    )
    permitted_connection = ws_factory()
    assert await permitted_connection.open(
        query_params={"ticket": permitted_user_ticket}
    )

    # Both tickets minted above were redeemed by the handshake (the rejected one is
    # consumed on redemption, before the permission check refuses it), so the store is left
    # exactly as it was found.
    assert outstanding_ticket_count() == outstanding_tickets_before


async def test_a_redeemed_ticket_resolves_to_exactly_its_own_user(cold_login):
    """A redeemed ticket resolves to the one user it was issued for and to nobody else.

    This is the direct-at-the-service counterpart to the socket test above: it pins the
    identity binding to a specific user by resolving the redeemed user ID through the same
    lookup the handshake path uses (users_service.get_user_by_user_id) and comparing the
    result against that same user's own /api/users/me.
    """
    client, _token = await cold_login("operator", "operator")
    own_user = (await client.get("/api/users/me")).json()

    ticket = (await client.post(TICKET_PATH)).json()["ticket"]
    redeemed_user_id = server_singletons.websocket_tickets_service.redeem_ticket(
        ticket=ticket,
    )

    # The redeemed value must be the user ID the websocket handshake path resolves
    # sessions with, and it must resolve back to the caller and to nobody else.
    assert redeemed_user_id == own_user["user_id"]

    redeemed_user = server_singletons.users_service.get_user_by_user_id(
        user_id=redeemed_user_id,
    )
    assert str(redeemed_user.user_id) == own_user["user_id"]
    assert redeemed_user.username == own_user["username"]


async def test_two_users_tickets_resolve_to_two_different_users(cold_login):
    """Two different users' tickets resolve to two different users.

    Complements the single-user resolution test: it is not enough that a ticket resolves
    to its own user in isolation, distinct issuers must resolve to distinct identities, or
    the binding could be collapsing everyone onto one account.
    """
    admin_client, _admin_token = await cold_login("admin", "admin")
    operator_client, _operator_token = await cold_login("operator", "operator")

    admin_user = (await admin_client.get("/api/users/me")).json()
    operator_user = (await operator_client.get("/api/users/me")).json()
    assert admin_user["user_id"] != operator_user["user_id"]

    admin_ticket = (await admin_client.post(TICKET_PATH)).json()["ticket"]
    operator_ticket = (await operator_client.post(TICKET_PATH)).json()["ticket"]
    assert admin_ticket != operator_ticket

    admin_resolved = server_singletons.users_service.get_user_by_user_id(
        user_id=server_singletons.websocket_tickets_service.redeem_ticket(
            ticket=admin_ticket
        ),
    )
    operator_resolved = server_singletons.users_service.get_user_by_user_id(
        user_id=server_singletons.websocket_tickets_service.redeem_ticket(
            ticket=operator_ticket
        ),
    )

    assert str(admin_resolved.user_id) == admin_user["user_id"]
    assert str(operator_resolved.user_id) == operator_user["user_id"]
    assert admin_resolved.user_id != operator_resolved.user_id
