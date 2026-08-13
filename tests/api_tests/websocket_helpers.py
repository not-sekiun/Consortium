# Shared helpers for the websocket events API e2e tests. Both test_events_api.py and
# test_websocket_authentication_e2e.py drive the /api/ws/events handshake through the
# same ASGI transport, the same controllable clock for ticket expiry, and the same small
# credential/ticket utilities, so those live here as the single source of truth rather
# than being duplicated per module.

import asyncio
import json
import time
import urllib.parse

import jwt

import consortium.server.server_singletons as server_singletons
from consortium.server.server_jwt_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_SECRET_KEY,
)

TICKET_PATH = "/api/ws/ticket"

UNKNOWN_ACCESS_TOKEN = "00000000-0000-0000-0000-000000000000"


# ---------------------------------------------------------------------------
# Minimal async ASGI WebSocket test transport
# ---------------------------------------------------------------------------


class WebSocketSession:
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
            # Percent-encoded exactly as a real client would send it, so the handshake
            # credential carried in the query string (a websocket ticket) reaches the
            # endpoint through the same parsing a browser's handshake would go through.
            # Defaults to no query string at all, which is a handshake presenting no
            # credential and must therefore be rejected.
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


# ---------------------------------------------------------------------------
# Controllable clock for ticket expiry
# ---------------------------------------------------------------------------


class FakeClock:
    # A controllable stand-in for the `time` module the tickets service reads, so ticket
    # expiry can be driven explicitly and never by sleeping. Mirrors the fake clock in
    # tests/services_tests/test_websocket_tickets_service.py.
    def __init__(self):
        self._now = time.monotonic()

    def monotonic(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


# ---------------------------------------------------------------------------
# Credential / ticket utilities
# ---------------------------------------------------------------------------


def forge_jwt(access_token: str) -> str:
    # Create a validly-signed JWT with the given access token as 'sub'.
    return jwt.encode(
        {"sub": access_token},
        JSON_WEB_TOKEN_SECRET_KEY,
        algorithm=JSON_WEB_TOKEN_ALGORITHMS[0],
    )


def bearer(token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}"}


def extract_token(client) -> str:
    return client.headers["Authorization"].split(" ", 1)[1]


def access_token_of(client) -> str:
    # The JWT `sub` claim of a logged-in client: the value tickets are bound to.
    return jwt.decode(
        jwt=extract_token(client),
        key=JSON_WEB_TOKEN_SECRET_KEY,
        algorithms=JSON_WEB_TOKEN_ALGORITHMS,
    )["sub"]


async def issue_ticket_over_http(client) -> str:
    # Mints a ticket the way every caller has to: an ordinary authenticated HTTP call,
    # whose Authorization header is the one place the token can still travel.
    response = await client.post(TICKET_PATH)
    assert response.status_code == 200, response.text
    return response.json()["ticket"]


async def open_with_ticket(ws, client) -> bool:
    # Open `ws` with a ticket freshly minted for `client`, the only way in. A ticket
    # authenticates exactly one handshake, so each session a test opens mints one of its
    # own: there is deliberately no shared ticket to hand around.
    return await ws.open(query_params={"ticket": await issue_ticket_over_http(client)})


def outstanding_ticket_count() -> int:
    # Reaches into the ticket store so a test can assert that a rejected request minted
    # nothing at all, rather than only that it got an error response back.
    return len(server_singletons.websocket_tickets_service._tickets)
