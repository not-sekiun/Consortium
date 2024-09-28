import json

import websockets

from consortium.client.exceptions.client_websocket_api_connection_exceptions import (
    ClientWebsocketsAPIConnectionAlreadyConnectedError,
    ClientWebsocketsAPIConnectionNotConnectedError,
    InvalidServerWebsocketAPIConnectionResponseError,
)


class ClientWebsocketsAPIConnection:
    def __init__(self, json_web_token: str):
        self._json_web_token = json_web_token

        self.connected = False

    async def connect(self):
        if self.connected:
            raise ClientWebsocketsAPIConnectionAlreadyConnectedError

        websocket = await websockets.connect(
            "ws://localhost:9999/api/events",
            extra_headers={"Authorization": f"Bearer {self._json_web_token}"},
        )

        self._websocket = websocket
        self.connected = True

    async def disconnect(self):
        if not self.connected:
            raise ClientWebsocketsAPIConnectionNotConnectedError

        await self._websocket.close()

        self.connected = False

    async def send_message(
        self,
        action: str,
        events: list[str] = None,
    ):
        if not self.connected:
            raise ClientWebsocketsAPIConnectionNotConnectedError

        if events is None:
            await self._websocket.send(json.dumps({"action": action}))
        else:
            await self._websocket.send(json.dumps({"action": action, "events": events}))

    async def recv_message(self):
        if not self.connected:
            raise ClientWebsocketsAPIConnectionNotConnectedError

        message = await self._websocket.recv()

        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            raise InvalidServerWebsocketAPIConnectionResponseError

        return message
