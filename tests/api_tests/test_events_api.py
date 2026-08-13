"""E2E tests for the WebSocket events API (/api/ws/events) and the websocket ticket
issuing endpoint that authenticates handshakes to it (/api/ws/ticket)."""

import json

import httpx
import pytest

import consortium.server.server_singletons as server_singletons
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.services.websocket_tickets_service import (
    TICKET_TIME_TO_LIVE_SECONDS,
)
from tests.api_tests.common_json_response_schemas import FORBIDDEN_ERROR_JSON_SCHEMA
from tests.api_tests.utils import validate_response
from tests.api_tests.websocket_helpers import (
    TICKET_PATH as _TICKET_PATH,
    UNKNOWN_ACCESS_TOKEN as _UNKNOWN_ACCESS_TOKEN,
    access_token_of as _access_token_of,
    bearer as _bearer,
    extract_token as _extract_token,
    forge_jwt as _forge_jwt,
    issue_ticket_over_http as _issue_ticket_over_http,
    open_with_ticket as _open_with_ticket,
    outstanding_ticket_count as _outstanding_ticket_count,
)

# The ASGI transport (WebSocketSession), the controllable clock (FakeClock), and the
# fixtures wrapping them (ws, ws_factory, ticket_clock,
# spectator_role_without_events_websocket_permission) live in websocket_helpers.py and
# conftest.py respectively, shared with test_websocket_authentication_e2e.py.

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Authentication / connection tests  (lines 391-447)
# ---------------------------------------------------------------------------


async def test_connect_without_a_ticket_is_rejected(ws):
    accepted = await ws.open()
    assert not accepted
    assert ws.close_code == 1008


async def test_valid_authorization_header_without_a_ticket_is_rejected(
    ws, admin_client
):
    """The header path is gone: a handshake is authenticated by ticket or not at all.

    The header presented here is a genuine, unexpired one that authenticates every REST
    call the client makes (it is what mints the tickets the tests below connect with), so
    the rejection can only be the handshake refusing to consider it.
    """
    accepted = await ws.open(headers=_bearer(_extract_token(admin_client)))

    assert not accepted
    assert ws.close_code == 1008


@pytest.mark.parametrize(
    "authorization_header_value",
    [
        "Basic dXNlcjpwYXNz",
        "Bearer this.is.not.a.valid.jwt",
        f"Bearer {_forge_jwt(_UNKNOWN_ACCESS_TOKEN)}",
    ],
)
async def test_handshake_ignores_any_authorization_header_it_is_given(
    ws,
    authorization_header_value,
):
    # The shapes of header that the handshake used to parse and reject one by one (a
    # non-bearer scheme, an unparseable token, a validly signed token for nobody) are now
    # refused for one reason only: no ticket was presented. None of them may be treated as
    # a credential, and none of them may make the handshake fail in some other way, such as
    # a JSON Web Token decode error escaping as a 500.
    accepted = await ws.open(headers={"authorization": authorization_header_value})

    assert not accepted
    assert ws.close_code == 1008


async def test_connect_with_a_ticket_for_an_unknown_access_token_is_rejected(ws):
    # A ticket that redeems fine but whose access token matches no logged-in user: the
    # user lookup after redemption is what has to reject this, not the redemption.
    ticket = server_singletons.websocket_tickets_service.issue_ticket(
        access_token=_UNKNOWN_ACCESS_TOKEN,
    )

    accepted = await ws.open(query_params={"ticket": ticket})

    assert not accepted
    assert ws.close_code == 1008


async def test_authenticated_admin_can_connect_and_disconnect(ws, admin_client):
    accepted = await _open_with_ticket(ws, admin_client)
    assert accepted
    await ws.close()


async def test_authenticated_operator_can_connect(ws, operator_client):
    accepted = await _open_with_ticket(ws, operator_client)
    assert accepted


async def test_authenticated_spectator_can_connect(ws, spectator_client):
    accepted = await _open_with_ticket(ws, spectator_client)
    assert accepted


# ---------------------------------------------------------------------------
# get_all_events action  (lines 197-204)
# ---------------------------------------------------------------------------


async def test_get_all_events_returns_every_event_type(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"action": "get_all_events"})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is True
    assert sorted(response["data"]) == sorted(str(et) for et in EventType)


# ---------------------------------------------------------------------------
# get_subscribed_events action  (lines 206-215)
# ---------------------------------------------------------------------------


async def test_get_subscribed_events_returns_empty_before_any_subscription(
    ws, admin_client
):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"action": "get_subscribed_events"})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is True
    assert response["data"] == []


async def test_get_subscribed_events_reflects_subscription(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    event = str(EventType.START_SERVER)
    await ws.send_json({"action": "subscribe", "events": [event]})
    await ws.receive_json()  # consume subscribe success

    await ws.send_json({"action": "get_subscribed_events"})
    response = await ws.receive_json()

    assert response["success"] is True
    assert event in response["data"]


# ---------------------------------------------------------------------------
# get_unsubscribed_events action  (lines 217-226)
# ---------------------------------------------------------------------------


async def test_get_unsubscribed_events_returns_all_events_before_subscription(
    ws, admin_client
):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"action": "get_unsubscribed_events"})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is True
    assert sorted(response["data"]) == sorted(str(et) for et in EventType)


async def test_get_unsubscribed_events_excludes_subscribed_event(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    event = str(EventType.STOP_SERVER)
    await ws.send_json({"action": "subscribe", "events": [event]})
    await ws.receive_json()

    await ws.send_json({"action": "get_unsubscribed_events"})
    response = await ws.receive_json()

    assert response["success"] is True
    assert event not in response["data"]


# ---------------------------------------------------------------------------
# subscribe action  (lines 228-276)
# ---------------------------------------------------------------------------


async def test_subscribe_to_valid_event_succeeds(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json(
        {"action": "subscribe", "events": [str(EventType.AGENT_REGISTERED)]}
    )
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is True


async def test_subscribe_to_multiple_events_at_once(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    events = [str(EventType.LISTENER_CREATED), str(EventType.LISTENER_REMOVED)]
    await ws.send_json({"action": "subscribe", "events": events})
    response = await ws.receive_json()

    assert response["success"] is True

    await ws.send_json({"action": "get_subscribed_events"})
    sub_response = await ws.receive_json()
    for event in events:
        assert event in sub_response["data"]


async def test_subscribe_to_invalid_event_type_returns_error(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"action": "subscribe", "events": ["NOT_A_REAL_EVENT"]})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is False
    assert len(response["errors"]) == 1
    assert response["errors"][0]["code"] == "INVALID_EVENT_TYPE_ERROR"
    assert response["errors"][0]["detail"] == {"event": "NOT_A_REAL_EVENT"}


async def test_subscribe_to_multiple_invalid_events_returns_one_error_per_event(
    ws, admin_client
):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"action": "subscribe", "events": ["BAD_1", "BAD_2"]})
    response = await ws.receive_json()

    assert response["success"] is False
    assert len(response["errors"]) == 2
    codes = {e["code"] for e in response["errors"]}
    assert codes == {"INVALID_EVENT_TYPE_ERROR"}


async def test_subscribe_twice_to_same_event_returns_already_subscribed_error(
    ws, admin_client
):
    await _open_with_ticket(ws, admin_client)

    event = str(EventType.PAYLOAD_CREATED)
    await ws.send_json({"action": "subscribe", "events": [event]})
    await ws.receive_json()  # first subscribe succeeds

    await ws.send_json({"action": "subscribe", "events": [event]})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "ALREADY_SUBSCRIBED_TO_EVENT_ERROR"


# ---------------------------------------------------------------------------
# unsubscribe action  (lines 278-324)
# ---------------------------------------------------------------------------


async def test_unsubscribe_from_subscribed_event_succeeds(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    event = str(EventType.AGENT_CHECKED_IN)
    await ws.send_json({"action": "subscribe", "events": [event]})
    await ws.receive_json()

    await ws.send_json({"action": "unsubscribe", "events": [event]})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is True

    await ws.send_json({"action": "get_subscribed_events"})
    sub_response = await ws.receive_json()
    assert event not in sub_response["data"]


async def test_unsubscribe_from_invalid_event_type_returns_error(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"action": "unsubscribe", "events": ["NOT_A_REAL_EVENT"]})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_EVENT_TYPE_ERROR"


async def test_unsubscribe_from_not_subscribed_event_returns_error(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json(
        {"action": "unsubscribe", "events": [str(EventType.USER_LOGGED_OUT)]}
    )
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "NOT_SUBSCRIBED_TO_EVENT_ERROR"


async def test_unsubscribe_from_multiple_not_subscribed_events_returns_multiple_errors(
    ws, admin_client
):
    await _open_with_ticket(ws, admin_client)

    events = [str(EventType.ASSET_CREATED), str(EventType.ASSET_DELETED)]
    await ws.send_json({"action": "unsubscribe", "events": events})
    response = await ws.receive_json()

    assert response["success"] is False
    assert len(response["errors"]) == 2


# ---------------------------------------------------------------------------
# Message format validation  (lines 331-366)
# ---------------------------------------------------------------------------


async def test_action_message_with_unknown_action_value_returns_format_error(
    ws, admin_client
):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"action": "do_something_unknown"})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_MESSAGE_FORMAT_ERROR"


async def test_subscribe_without_events_field_returns_format_error(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    # The JSON schema requires "events" when action is "subscribe".
    await ws.send_json({"action": "subscribe"})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_MESSAGE_FORMAT_ERROR"


async def test_unsubscribe_without_events_field_returns_format_error(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"action": "unsubscribe"})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_MESSAGE_FORMAT_ERROR"


async def test_message_without_action_field_returns_format_error(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    await ws.send_json({"events": [str(EventType.START_SERVER)]})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_MESSAGE_FORMAT_ERROR"


# ---------------------------------------------------------------------------
# Event reception  (line 139-145)
# ---------------------------------------------------------------------------


async def test_subscribed_client_receives_triggered_event(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    event_type = EventType.ARTIFACT_CREATED
    await ws.send_json({"action": "subscribe", "events": [str(event_type)]})
    await ws.receive_json()  # consume subscribe success

    await server_singletons.events_service.trigger_event(
        event_type=event_type,
        message="test trigger",
        data={"key": "value"},
    )

    event_msg = await ws.receive_json()

    assert event_msg["type"] == "event"
    assert event_msg["event_type"] == str(event_type)
    assert event_msg["message"] == "test trigger"
    assert event_msg["data"] == {"key": "value"}


async def test_client_does_not_receive_events_it_did_not_subscribe_to(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    # Subscribe to one event type
    await ws.send_json(
        {"action": "subscribe", "events": [str(EventType.ARTIFACT_UPDATED)]}
    )
    await ws.receive_json()

    # Trigger a DIFFERENT event type
    await server_singletons.events_service.trigger_event(
        event_type=EventType.ARTIFACT_DELETED,
        message="different event",
        data={},
    )

    # No message should have been pushed into this session's queue
    assert ws._from_app.empty()


async def test_after_unsubscribe_client_no_longer_receives_event(ws, admin_client):
    await _open_with_ticket(ws, admin_client)

    event_type = EventType.PAYLOAD_UPDATED
    await ws.send_json({"action": "subscribe", "events": [str(event_type)]})
    await ws.receive_json()
    await ws.send_json({"action": "unsubscribe", "events": [str(event_type)]})
    await ws.receive_json()

    await server_singletons.events_service.trigger_event(
        event_type=event_type,
        message="should not arrive",
        data={},
    )

    assert ws._from_app.empty()


# ---------------------------------------------------------------------------
# Multiple connections
# ---------------------------------------------------------------------------


async def test_multiple_clients_both_receive_same_event(
    ws_factory, admin_client, operator_client
):
    ws1 = ws_factory()
    ws2 = ws_factory()
    await _open_with_ticket(ws1, admin_client)
    await _open_with_ticket(ws2, operator_client)

    event_type = EventType.ASSET_UPDATED
    for ws in (ws1, ws2):
        await ws.send_json({"action": "subscribe", "events": [str(event_type)]})
        await ws.receive_json()

    await server_singletons.events_service.trigger_event(
        event_type=event_type,
        message="broadcast",
        data={},
    )

    msg1 = await ws1.receive_json()
    msg2 = await ws2.receive_json()
    assert msg1["type"] == "event"
    assert msg2["type"] == "event"


# ---------------------------------------------------------------------------
# Disconnect cleanup  (lines 367-376)
# ---------------------------------------------------------------------------


async def test_disconnect_deregisters_event_handlers(ws, admin_client):
    """
    After a client disconnects, triggering an event it was subscribed to must
    not call its (now-closed) handler.  If cleanup failed, trigger_event would
    try to send on a closed WebSocket and raise an ExceptionGroup.
    """
    await _open_with_ticket(ws, admin_client)

    event_type = EventType.PAYLOAD_DELETED
    await ws.send_json({"action": "subscribe", "events": [str(event_type)]})
    await ws.receive_json()

    # Disconnect - this should deregister the handler
    await ws.close()

    # If the handler were still registered this would attempt to send on the
    # closed socket and raise an ExceptionGroup.
    await server_singletons.events_service.trigger_event(
        event_type=event_type,
        message="post-disconnect trigger",
        data={},
    )


async def test_disconnect_without_subscription_does_not_error(ws, admin_client):
    """Disconnect with no subscriptions should complete without errors."""
    await _open_with_ticket(ws, admin_client)
    await ws.close()


# ---------------------------------------------------------------------------
# Websocket ticket issuance  (POST /api/ws/ticket)
# ---------------------------------------------------------------------------

WEBSOCKET_TICKET_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "ticket": {"type": "string"},
        "time_to_live_seconds": {"type": "integer"},
    },
    "required": ["ticket", "time_to_live_seconds"],
    "additionalProperties": False,
}


@pytest.fixture
async def unauthenticated_client(app):
    """An httpx client bound to the app that sends no Authorization header."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


async def test_issue_ticket_without_authorization_header_returns_401(
    unauthenticated_client,
):
    response = await unauthenticated_client.post(_TICKET_PATH)
    assert response.status_code == 401


async def test_issue_ticket_with_malformed_jwt_returns_401(unauthenticated_client):
    response = await unauthenticated_client.post(
        _TICKET_PATH,
        headers=_bearer("this.is.not.a.valid.jwt"),
    )
    assert response.status_code == 401


async def test_issue_ticket_with_unknown_access_token_returns_401(
    unauthenticated_client,
):
    # Validly signed JWT whose subject matches no logged-in user.
    fake_jwt = _forge_jwt(_UNKNOWN_ACCESS_TOKEN)
    response = await unauthenticated_client.post(
        _TICKET_PATH,
        headers=_bearer(fake_jwt),
    )
    assert response.status_code == 401


async def test_issue_ticket_without_use_events_websocket_permission_returns_403(
    spectator_client,
    spectator_role_without_events_websocket_permission,
):
    """A caller who may not use the websocket must not be able to get a ticket for it.

    This is the security crux of the endpoint: were issuance authorized by anything
    weaker than the permission the websocket endpoint itself checks, a ticket would be a
    way around that check.
    """
    outstanding_tickets_before = _outstanding_ticket_count()

    validate_response(
        test_response=await spectator_client.post(_TICKET_PATH),
        expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
        expected_status_code=403,
    )

    # The request must be refused before a ticket is minted, not merely have its response
    # thrown away: nothing may reach the store on the unauthorized path.
    assert _outstanding_ticket_count() == outstanding_tickets_before


async def test_issue_ticket_succeeds_again_once_the_permission_is_restored(
    spectator_client,
):
    # Guards the test above against passing for the wrong reason: the same caller, with
    # the permission back in place, is served a ticket, so the 403 can only have come
    # from the missing permission.
    response = validate_response(
        test_response=await spectator_client.post(_TICKET_PATH),
        expected_json_schema=WEBSOCKET_TICKET_JSON_SCHEMA,
        expected_status_code=200,
    )
    server_singletons.websocket_tickets_service.redeem_ticket(
        ticket=response.json()["ticket"],
    )


async def test_issued_ticket_redeems_to_the_callers_own_session(client):
    own_user = (await client.get("/api/users/me")).json()

    response = validate_response(
        test_response=await client.post(_TICKET_PATH),
        expected_json_schema=WEBSOCKET_TICKET_JSON_SCHEMA,
        expected_status_code=200,
    )
    ticket = response.json()["ticket"]
    assert ticket

    redeemed_access_token = server_singletons.websocket_tickets_service.redeem_ticket(
        ticket=ticket
    )
    # The redeemed value must be the access token the websocket handshake path resolves
    # users with (the JWT's `sub` claim), and it must resolve back to the caller and to
    # nobody else.
    redeemed_user = server_singletons.users_service.get_user_by_access_token(
        redeemed_access_token,
    )
    assert redeemed_access_token == str(redeemed_user.json_web_token.subject)
    assert str(redeemed_user.user_id) == own_user["user_id"]
    assert redeemed_user.username == own_user["username"]


async def test_issued_ticket_reports_the_services_time_to_live(admin_client):
    response = validate_response(
        test_response=await admin_client.post(_TICKET_PATH),
        expected_json_schema=WEBSOCKET_TICKET_JSON_SCHEMA,
        expected_status_code=200,
    )
    assert response.json()["time_to_live_seconds"] == TICKET_TIME_TO_LIVE_SECONDS

    server_singletons.websocket_tickets_service.redeem_ticket(
        ticket=response.json()["ticket"],
    )


async def test_two_issued_tickets_are_distinct(admin_client):
    first = (await admin_client.post(_TICKET_PATH)).json()["ticket"]
    second = (await admin_client.post(_TICKET_PATH)).json()["ticket"]

    assert first != second

    for ticket in (first, second):
        server_singletons.websocket_tickets_service.redeem_ticket(ticket=ticket)


async def test_ticket_route_is_published_with_a_clean_operation_id(app):
    openapi_schema = app.openapi()

    assert _TICKET_PATH in openapi_schema["paths"]
    post_operation = openapi_schema["paths"][_TICKET_PATH]["post"]
    # `use_route_name_as_operation_id` turns the route name into the operationId, so
    # generated clients get `issue_websocket_ticket` rather than a path-mangled name like
    # `issue_websocket_ticket_api_ws_ticket_post`.
    assert post_operation["operationId"] == "issue_websocket_ticket"
    assert "WebsocketTicketModel" in json.dumps(post_operation["responses"]["200"])


# ---------------------------------------------------------------------------
# Ticket authenticated handshakes  (GET /api/ws/events?ticket=...)
# ---------------------------------------------------------------------------


async def test_connect_with_ticket_and_no_authorization_header_succeeds(
    ws, admin_client
):
    """The only handshake there is, end to end: no headers at all, just a ticket.

    The socket then has to be usable, not merely accepted, so this drives a subscribe and
    receives a real event over it.
    """
    ticket = await _issue_ticket_over_http(admin_client)

    accepted = await ws.open(headers={}, query_params={"ticket": ticket})

    assert accepted

    event_type = EventType.ASSET_CREATED
    await ws.send_json({"action": "subscribe", "events": [str(event_type)]})
    subscribe_response = await ws.receive_json()
    assert subscribe_response["success"] is True

    await server_singletons.events_service.trigger_event(
        event_type=event_type,
        message="ticket authenticated",
        data={"key": "value"},
    )

    event_message = await ws.receive_json()
    assert event_message["type"] == "event"
    assert event_message["event_type"] == str(event_type)
    assert event_message["message"] == "ticket authenticated"


async def test_replayed_ticket_is_rejected(ws_factory, admin_client):
    """Single use is enforced at the handshake: the second use of a ticket is refused.

    The first connection is asserted to be accepted so the rejection of the second can
    only be the replay, not a ticket that was never good in the first place.
    """
    ticket = await _issue_ticket_over_http(admin_client)

    first_connection = ws_factory()
    assert await first_connection.open(query_params={"ticket": ticket})

    replayed_connection = ws_factory()
    accepted = await replayed_connection.open(query_params={"ticket": ticket})

    assert not accepted
    assert replayed_connection.close_code == 1008


async def test_expired_ticket_is_rejected(ws, admin_client, ticket_clock):
    ticket = await _issue_ticket_over_http(admin_client)

    ticket_clock.advance(TICKET_TIME_TO_LIVE_SECONDS + 1)

    accepted = await ws.open(query_params={"ticket": ticket})

    assert not accepted
    assert ws.close_code == 1008


async def test_ticket_issued_just_inside_its_lifetime_still_connects(
    ws, admin_client, ticket_clock
):
    # Guards the expiry test against passing for the wrong reason: the same flow, with the
    # clock moved to just short of the deadline, is still accepted, so the rejection above
    # can only have come from the ticket having expired.
    ticket = await _issue_ticket_over_http(admin_client)

    ticket_clock.advance(TICKET_TIME_TO_LIVE_SECONDS - 1)

    assert await ws.open(query_params={"ticket": ticket})


async def test_unknown_ticket_is_rejected(ws):
    accepted = await ws.open(
        query_params={"ticket": "not-a-ticket-that-was-ever-issued"}
    )

    assert not accepted
    assert ws.close_code == 1008


async def test_empty_ticket_parameter_is_rejected(ws):
    # An empty ticket is still a ticket that was presented, so it is redeemed (and fails)
    # rather than being treated as absent, and either way it never authenticates anything.
    accepted = await ws.open(query_params={"ticket": ""})

    assert not accepted
    assert ws.close_code == 1008


async def test_use_events_websocket_permission_is_enforced_on_the_handshake(
    ws,
    spectator_client,
    spectator_role_without_events_websocket_permission,
):
    """Redeeming a ticket is authentication only: the permission is checked after it.

    The ticket here is minted straight from the service rather than over
    POST /api/ws/ticket, because that endpoint requires the very permission this test
    strips. Handing the handshake a ticket that could not legitimately have been obtained
    is the stronger test anyway: it proves the websocket endpoint enforces the permission
    itself rather than leaning on issuance having enforced it.
    """
    outstanding_tickets_before = _outstanding_ticket_count()

    ticket = server_singletons.websocket_tickets_service.issue_ticket(
        access_token=_access_token_of(spectator_client),
    )

    accepted = await ws.open(query_params={"ticket": ticket})

    assert not accepted
    assert ws.close_code == 1008
    # Redeeming is consuming: the ticket minted above redeemed fine and was then refused by
    # the permission check, and it is deliberately not put back, so the store is left
    # exactly as it was found.
    assert _outstanding_ticket_count() == outstanding_tickets_before


async def test_handshake_connects_once_the_permission_is_restored(ws, spectator_client):
    # Guards the test above against passing for the wrong reason: the same user, over the
    # same credential path, is accepted once the permission is back, so the rejection can
    # only have come from the missing permission.
    assert await _open_with_ticket(ws, spectator_client)
