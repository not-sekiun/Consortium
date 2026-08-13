"""E2E tests for the WebSocket events API (/api/ws/events) and the websocket ticket
issuing endpoint that authenticates handshakes to it (/api/ws/ticket)."""

import asyncio
import json
import time
import urllib.parse

import httpx
import jwt
import pytest

import consortium.server.server_singletons as server_singletons
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_jwt_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_SECRET_KEY,
)
from consortium.server.services import websocket_tickets_service as tickets_module
from consortium.server.services.websocket_tickets_service import (
    TICKET_TIME_TO_LIVE_SECONDS,
)
from tests.api_tests.common_json_response_schemas import FORBIDDEN_ERROR_JSON_SCHEMA
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Minimal async ASGI WebSocket test transport
# ---------------------------------------------------------------------------


class _WebSocketSession:
    """
    Drives a FastAPI WebSocket endpoint via the ASGI interface directly, using
    asyncio.Queue pairs for bidirectional message passing.  No network I/O or
    threads are involved, so it cooperates cleanly with the anyio event loop
    used by the rest of the test suite.
    """

    def __init__(self, app):
        self._app = app
        self._to_app: asyncio.Queue = asyncio.Queue()
        self._from_app: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self.close_code: int | None = None

    def _build_scope(
        self,
        headers: dict[str, str],
        query_params: dict[str, str],
    ) -> dict:
        return {
            "type": "websocket",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "scheme": "ws",
            "path": "/api/ws/events",
            # Percent-encoded exactly as a real client would send it, so a handshake
            # credential carried in the query string (a websocket ticket) reaches the
            # endpoint through the same parsing a browser's handshake would go through.
            # Defaults to no query string at all, which is what every header
            # authenticated test drives.
            "query_string": urllib.parse.urlencode(query_params).encode(),
            "root_path": "",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            "server": ("testclient", 80),
            "client": ("testclient", 12345),
        }

    async def open(
        self,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
    ) -> bool:
        """
        Perform the WebSocket handshake.  Returns True when accepted, False
        when rejected (close_code is set in that case).

        Starlette's WebSocket.close() calls accept() internally before closing
        when the connection is still in the CONNECTING state.  That means auth
        failures produce an accept frame immediately followed by a close frame.
        Both cases are handled here.
        """
        scope = self._build_scope(headers or {}, query_params or {})

        async def receive():
            return await self._to_app.get()

        async def send(message):
            await self._from_app.put(message)

        self._task = asyncio.create_task(self._app(scope, receive, send))

        await self._to_app.put({"type": "websocket.connect"})

        # Wait for the first ASGI message from the app.  Awaiting get() here
        # yields the event loop to the app task so it can process the connect
        # message and enqueue its response(s) before we resume.
        first = await asyncio.wait_for(self._from_app.get(), timeout=5.0)

        if first["type"] == "websocket.close":
            self.close_code = first.get("code", 1000)
            await asyncio.wait_for(self._task, timeout=2.0)
            return False

        assert first["type"] == "websocket.accept", (
            f"Unexpected first message from app: {first}"
        )

        # When Starlette auto-accepts before closing (rejection path), the
        # close frame is already in the queue by the time we reach here.
        if not self._from_app.empty():
            second = self._from_app.get_nowait()
            if second["type"] == "websocket.close":
                self.close_code = second.get("code", 1000)
                await asyncio.wait_for(self._task, timeout=2.0)
                return False

        return True

    async def send_json(self, data: dict) -> None:
        await self._to_app.put(
            {
                "type": "websocket.receive",
                "text": json.dumps(data),
                "bytes": None,
            }
        )

    async def receive_json(self) -> dict:
        msg = await asyncio.wait_for(self._from_app.get(), timeout=5.0)
        if msg["type"] == "websocket.close":
            raise ConnectionError(
                f"WebSocket closed unexpectedly (code={msg.get('code', 1000)})"
            )
        text = msg.get("text") or (msg.get("bytes") or b"").decode()
        return json.loads(text)

    async def close(self) -> None:
        await self._to_app.put({"type": "websocket.disconnect", "code": 1000})
        if self._task:
            await asyncio.wait_for(self._task, timeout=2.0)


@pytest.fixture
async def ws_factory(app):
    """
    Factory fixture for creating `_WebSocketSession` instances bound to `app`.

    Every session produced by the returned factory is tracked and closed
    automatically on teardown, so tests no longer need to call `await
    ws.close()` themselves (closing early inside a test, e.g. to assert
    post-disconnect behavior, still works fine - `close()` is a no-op on an
    already-finished session).
    """
    sessions: list[_WebSocketSession] = []

    def _make() -> _WebSocketSession:
        ws = _WebSocketSession(app)
        sessions.append(ws)
        return ws

    yield _make

    for ws in sessions:
        await ws.close()


@pytest.fixture
async def ws(ws_factory):
    """A single, unopened `_WebSocketSession` for tests that need only one."""
    return ws_factory()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _forge_jwt(access_token: str) -> str:
    """Create a validly-signed JWT with the given access token as 'sub'."""
    return jwt.encode(
        {"sub": access_token},
        JSON_WEB_TOKEN_SECRET_KEY,
        algorithm=JSON_WEB_TOKEN_ALGORITHMS[0],
    )


def _bearer(token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}"}


def _extract_token(client) -> str:
    return client.headers["Authorization"].split(" ", 1)[1]


def _access_token_of(client) -> str:
    """The JWT `sub` claim of a logged-in client: the value tickets are bound to."""
    return jwt.decode(
        jwt=_extract_token(client),
        key=JSON_WEB_TOKEN_SECRET_KEY,
        algorithms=JSON_WEB_TOKEN_ALGORITHMS,
    )["sub"]


# ---------------------------------------------------------------------------
# Authentication / connection tests  (lines 391-447)
# ---------------------------------------------------------------------------


async def test_connect_without_authorization_header_is_rejected(ws):
    accepted = await ws.open(headers={})
    assert not accepted
    assert ws.close_code == 1008


async def test_connect_with_non_bearer_scheme_is_rejected(ws):
    accepted = await ws.open(headers={"authorization": "Basic dXNlcjpwYXNz"})
    assert not accepted
    assert ws.close_code == 1008


async def test_connect_with_malformed_jwt_is_rejected(ws):
    accepted = await ws.open(headers=_bearer("this.is.not.a.valid.jwt"))
    assert not accepted
    assert ws.close_code == 1008


async def test_connect_with_unknown_access_token_is_rejected(ws):
    # Validly signed JWT but the access token doesn't match any logged-in user.
    fake_jwt = _forge_jwt("00000000-0000-0000-0000-000000000000")
    accepted = await ws.open(headers=_bearer(fake_jwt))
    assert not accepted
    assert ws.close_code == 1008


async def test_authenticated_admin_can_connect_and_disconnect(ws, admin_client):
    accepted = await ws.open(headers=_bearer(_extract_token(admin_client)))
    assert accepted
    await ws.close()


async def test_authenticated_operator_can_connect(ws, operator_client):
    accepted = await ws.open(headers=_bearer(_extract_token(operator_client)))
    assert accepted


async def test_authenticated_spectator_can_connect(ws, spectator_client):
    accepted = await ws.open(headers=_bearer(_extract_token(spectator_client)))
    assert accepted


# ---------------------------------------------------------------------------
# get_all_events action  (lines 197-204)
# ---------------------------------------------------------------------------


async def test_get_all_events_returns_every_event_type(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json({"action": "get_subscribed_events"})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is True
    assert response["data"] == []


async def test_get_subscribed_events_reflects_subscription(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json({"action": "get_unsubscribed_events"})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is True
    assert sorted(response["data"]) == sorted(str(et) for et in EventType)


async def test_get_unsubscribed_events_excludes_subscribed_event(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json(
        {"action": "subscribe", "events": [str(EventType.AGENT_REGISTERED)]}
    )
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is True


async def test_subscribe_to_multiple_events_at_once(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    events = [str(EventType.LISTENER_CREATED), str(EventType.LISTENER_REMOVED)]
    await ws.send_json({"action": "subscribe", "events": events})
    response = await ws.receive_json()

    assert response["success"] is True

    await ws.send_json({"action": "get_subscribed_events"})
    sub_response = await ws.receive_json()
    for event in events:
        assert event in sub_response["data"]


async def test_subscribe_to_invalid_event_type_returns_error(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json({"action": "subscribe", "events": ["BAD_1", "BAD_2"]})
    response = await ws.receive_json()

    assert response["success"] is False
    assert len(response["errors"]) == 2
    codes = {e["code"] for e in response["errors"]}
    assert codes == {"INVALID_EVENT_TYPE_ERROR"}


async def test_subscribe_twice_to_same_event_returns_already_subscribed_error(
    ws, admin_client
):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json({"action": "unsubscribe", "events": ["NOT_A_REAL_EVENT"]})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_EVENT_TYPE_ERROR"


async def test_unsubscribe_from_not_subscribed_event_returns_error(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json(
        {"action": "unsubscribe", "events": [str(EventType.USER_LOGGED_OUT)]}
    )
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "NOT_SUBSCRIBED_TO_EVENT_ERROR"


async def test_unsubscribe_from_multiple_not_subscribed_events_returns_multiple_errors(
    ws, admin_client
):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json({"action": "do_something_unknown"})
    response = await ws.receive_json()

    assert response["type"] == "response"
    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_MESSAGE_FORMAT_ERROR"


async def test_subscribe_without_events_field_returns_format_error(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    # The JSON schema requires "events" when action is "subscribe".
    await ws.send_json({"action": "subscribe"})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_MESSAGE_FORMAT_ERROR"


async def test_unsubscribe_without_events_field_returns_format_error(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json({"action": "unsubscribe"})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_MESSAGE_FORMAT_ERROR"


async def test_message_without_action_field_returns_format_error(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json({"events": [str(EventType.START_SERVER)]})
    response = await ws.receive_json()

    assert response["success"] is False
    assert response["errors"][0]["code"] == "INVALID_MESSAGE_FORMAT_ERROR"


# ---------------------------------------------------------------------------
# Event reception  (line 139-145)
# ---------------------------------------------------------------------------


async def test_subscribed_client_receives_triggered_event(ws, admin_client):
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws1.open(headers=_bearer(_extract_token(admin_client)))
    await ws2.open(headers=_bearer(_extract_token(operator_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))

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
    await ws.open(headers=_bearer(_extract_token(admin_client)))
    await ws.close()


# ---------------------------------------------------------------------------
# Websocket ticket issuance  (POST /api/ws/ticket)
# ---------------------------------------------------------------------------

_TICKET_PATH = "/api/ws/ticket"

WEBSOCKET_TICKET_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "ticket": {"type": "string"},
        "time_to_live_seconds": {"type": "integer"},
    },
    "required": ["ticket", "time_to_live_seconds"],
    "additionalProperties": False,
}


def _outstanding_ticket_count() -> int:
    # Reaches into the ticket store so a test can assert that a rejected request minted
    # nothing at all, rather than only that it got an error response back.
    return len(server_singletons.websocket_tickets_service._tickets)


@pytest.fixture
async def unauthenticated_client(app):
    """An httpx client bound to the app that sends no Authorization header."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def spectator_role_without_events_websocket_permission(spectator_client):
    """Strips USE_EVENTS_WEBSOCKET from the spectator's role for the test's duration.

    All three default roles hold the permission, so a role that lacks it has to be
    manufactured. Only the authorization service's in-memory mapping is touched:
    `save_server_role_permissions` is never called, so data/server/role_permissions.json
    is left exactly as it was on disk.
    """
    role = (await spectator_client.get("/api/users/me")).json()["role"]
    permission = str(UserPermissions.USE_EVENTS_WEBSOCKET)
    authorization_service = server_singletons.authorization_service

    authorization_service.remove_permission_from_role(
        role=role,
        permission=permission,
    )
    assert not authorization_service.has_permission(role, permission)

    yield role

    authorization_service.add_permission_to_role(role=role, permission=permission)


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
    fake_jwt = _forge_jwt("00000000-0000-0000-0000-000000000000")
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


class _FakeClock:
    # A controllable stand-in for the `time` module the tickets service reads, so ticket
    # expiry can be driven explicitly and never by sleeping. Mirrors the fake clock in
    # tests/services_tests/test_websocket_tickets_service.py.
    def __init__(self):
        self._now = time.monotonic()

    def monotonic(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


@pytest.fixture
def ticket_clock(monkeypatch):
    """Replaces the clock the tickets service reads, for the test's duration."""
    fake_clock = _FakeClock()
    # The service's whole `time` name is swapped rather than `time.monotonic` being
    # patched on the real `time` module (which is what the service unit tests do). These
    # tests drive an asyncio event loop, and the loop reads `time.monotonic` for its own
    # timers: moving the real clock forward by a ticket lifetime would fire every pending
    # timeout in the loop as a side effect. Swapping the name confines the fake to the one
    # module under test. The service uses `time` for nothing but `monotonic`.
    monkeypatch.setattr(tickets_module, "time", fake_clock)
    return fake_clock


async def _issue_ticket_over_http(client) -> str:
    # Mints a ticket the way a browser would: an ordinary authenticated HTTP call, whose
    # Authorization header is the one place the token can still travel.
    response = await client.post(_TICKET_PATH)
    assert response.status_code == 200, response.text
    return response.json()["ticket"]


async def test_connect_with_ticket_and_no_authorization_header_succeeds(
    ws, admin_client
):
    """The browser case end to end: no handshake headers at all, just a ticket.

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


async def test_empty_ticket_parameter_does_not_fall_back_to_the_header(
    ws, admin_client
):
    # An empty ticket is still a ticket that was presented, so it is redeemed (and fails)
    # rather than being treated as absent and letting the header through.
    accepted = await ws.open(
        headers=_bearer(_extract_token(admin_client)),
        query_params={"ticket": ""},
    )

    assert not accepted
    assert ws.close_code == 1008


async def test_bad_ticket_alongside_a_valid_authorization_header_is_rejected(
    ws, admin_client
):
    """A failed ticket must never fall back to the Authorization header.

    The header presented here is a good one that authenticates on its own (proved by
    `test_authenticated_admin_can_connect_and_disconnect`), so acceptance here could only
    mean the bad ticket was silently ignored. Falling back would mask a bad or replayed
    ticket for any caller that also happens to carry a valid header.
    """
    accepted = await ws.open(
        headers=_bearer(_extract_token(admin_client)),
        query_params={"ticket": "not-a-ticket-that-was-ever-issued"},
    )

    assert not accepted
    assert ws.close_code == 1008


async def test_replayed_ticket_alongside_a_valid_authorization_header_is_rejected(
    ws_factory, admin_client
):
    # The same no-fallback property for the case the fallback would be most damaging in:
    # a genuine ticket being replayed by a caller who also holds a valid header.
    ticket = await _issue_ticket_over_http(admin_client)
    header = _bearer(_extract_token(admin_client))

    first_connection = ws_factory()
    assert await first_connection.open(headers=header, query_params={"ticket": ticket})

    replayed_connection = ws_factory()
    accepted = await replayed_connection.open(
        headers=header,
        query_params={"ticket": ticket},
    )

    assert not accepted
    assert replayed_connection.close_code == 1008


async def test_authorization_header_path_still_authenticates_and_drives_the_socket(
    ws, admin_client
):
    # The REPL client authenticates by header and is migrated to tickets separately, so
    # the header path has to keep working in full, not just to the point of acceptance.
    assert await ws.open(headers=_bearer(_extract_token(admin_client)))

    await ws.send_json({"action": "get_all_events"})
    response = await ws.receive_json()

    assert response["success"] is True


@pytest.mark.parametrize("credential", ["authorization_header", "ticket"])
async def test_use_events_websocket_permission_is_enforced_on_both_credential_paths(
    ws,
    spectator_client,
    spectator_role_without_events_websocket_permission,
    credential,
):
    """The permission check is shared, so it applies identically however you authenticate.

    Both credential sources resolve to an access token and then run one user lookup and
    one permission check, so a ticket can never be a way around a check that the header
    path applies. Parametrizing one test body over both credentials is the point: the same
    user, the same missing permission and the same expected rejection.
    """
    outstanding_tickets_before = _outstanding_ticket_count()

    if credential == "authorization_header":
        headers = _bearer(_extract_token(spectator_client))
        query_params = {}
    else:
        # Minted straight from the service rather than over POST /api/ws/ticket, because
        # that endpoint requires the very permission this test strips. Handing the
        # handshake a ticket that could not legitimately have been obtained is the
        # stronger test anyway: it proves the websocket endpoint enforces the permission
        # itself rather than leaning on issuance having enforced it.
        headers = {}
        query_params = {
            "ticket": server_singletons.websocket_tickets_service.issue_ticket(
                access_token=_access_token_of(spectator_client),
            )
        }

    accepted = await ws.open(headers=headers, query_params=query_params)

    assert not accepted
    assert ws.close_code == 1008
    # Redeeming is consuming: on the ticket path the ticket minted above redeemed fine and
    # was then refused by the permission check, and it is deliberately not put back, so the
    # store is left exactly as it was found.
    assert _outstanding_ticket_count() == outstanding_tickets_before


@pytest.mark.parametrize("credential", ["authorization_header", "ticket"])
async def test_both_credential_paths_connect_once_the_permission_is_restored(
    ws, spectator_client, credential
):
    # Guards the test above against passing for the wrong reason: the same user, over the
    # same two credential paths, is accepted once the permission is back, so the
    # rejections can only have come from the missing permission.
    if credential == "authorization_header":
        headers = _bearer(_extract_token(spectator_client))
        query_params = {}
    else:
        headers = {}
        query_params = {"ticket": await _issue_ticket_over_http(spectator_client)}

    assert await ws.open(headers=headers, query_params=query_params)
