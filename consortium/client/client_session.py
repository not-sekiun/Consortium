import uuid
from datetime import datetime

from consortium.client.client_rest_api import RestAPI
from consortium.client.client_websockets_api import (
    WebsocketsAPI,
)
from consortium.client.exceptions.client_session_exceptions import (
    ClientSessionAlreadyConnectedException,
    ClientSessionNotConnectedException,
)


class ClientSession:
    def __init__(
        self,
        username: str,
        password: str,
        remote_host: str,
        remote_port: int,
    ):
        self.client_session_id = uuid.uuid4()
        self.name = ""
        self.description = ""
        self.username = username
        self.password = password
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.connected = False
        self.datetime_connected = None

        self.rest_api = RestAPI(
            username=self.username,
            password=self.password,
            remote_host=self.remote_host,
            remote_port=self.remote_port,
        )
        self.websockets_api = WebsocketsAPI(
            remote_host=self.remote_host,
            remote_port=self.remote_port,
        )

    def __str__(self) -> str:
        return f"'{self.name}' ({self.client_session_id})"

    async def connect(self):
        if self.connected:
            raise ClientSessionAlreadyConnectedException

        await self.rest_api.connect()
        await self.websockets_api.connect(json_web_token=self.rest_api.json_web_token)

        self.datetime_connected = datetime.now()
        self.connected = True

    async def disconnect(self) -> None:
        if not self.connected:
            raise ClientSessionNotConnectedException

        await self.websockets_api.disconnect()
        await self.rest_api.disconnect()

        self.connected = False
