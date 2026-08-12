"""E2E tests for the WebSocket events API (/api/ws/events)."""

import asyncio
import json

import jwt
import pytest

import consortium.server.server_singletons as server_singletons
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.server_jwt_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_SECRET_KEY,
)

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

    def _build_scope(self, headers: dict[str, str]) -> dict:
        return {
            "type": "websocket",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "scheme": "ws",
            "path": "/api/ws/events",
            "query_string": b"",
            "root_path": "",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            "server": ("testclient", 80),
            "client": ("testclient", 12345),
        }

    async def open(self, headers: dict[str, str] | None = None) -> bool:
        """
        Perform the WebSocket handshake.  Returns True when accepted, False
        when rejected (close_code is set in that case).

        Starlette's WebSocket.close() calls accept() internally before closing
        when the connection is still in the CONNECTING state.  That means auth
        failures produce an accept frame immediately followed by a close frame.
        Both cases are handled here.
        """
        scope = self._build_scope(headers or {})

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
