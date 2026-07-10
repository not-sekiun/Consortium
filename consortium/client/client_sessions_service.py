import uuid
from typing import TYPE_CHECKING

from aiohttp.client_exceptions import ClientConnectorError
from loguru import logger
from websockets.exceptions import ConnectionClosed, InvalidHandshake

from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionConnectionError,
    ClientSessionNotFoundError,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class ClientSessionsService:
    def __init__(self):
        self._client_sessions = {}
        self._logger = logger.bind(
            logger_name=str(self),
        )

    def __str__(self) -> str:
        return "Client Sessions Service"

    def __repr__(self) -> str:
        return "ClientSessionsService()"

    def get_all_client_sessions(self) -> list[ClientSession]:
        all_client_sessions = list(self._client_sessions.values())
        self._logger.debug(
            f"Retrieved all client sessions ({len(all_client_sessions)} retrieved).",
        )
        return all_client_sessions

    def get_client_session_by_client_session_id(
        self,
        client_session_id: str | uuid.UUID,
    ) -> ClientSession:
        client_session_id = str(client_session_id)

        try:
            client_session = self._client_sessions[client_session_id]
        except KeyError:
            raise ClientSessionNotFoundError(
                client_session_id=client_session_id
            ) from None

        self._logger.debug(
            f"Retrieved client session: {repr(client_session)}",
        )
        return client_session

    # Create a new client session, attempt to connect to the server, and add it to
    # the internal dictionary of client sessions.
    async def create_client_session(
        self,
        username: str,
        password: str,
        remote_host: str,
        remote_port: int,
    ) -> ClientSession:
        # Importing here to avoid circular imports.
        from consortium.client.client_session import ClientSession

        client_session = ClientSession(
            username=username,
            password=password,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        self._logger.debug(
            f"Created client session: {client_session!r}",
        )

        try:
            # If credentials are invalid `InvalidRestAPICredentialsError` is raised
            # here
            await client_session.connect()
        except (
            ClientConnectorError,
            InvalidHandshake,
            ConnectionClosed,
        ) as exc:
            # The client session attempts to connect to the REST API first before the
            # websockets server. If the REST API connection fails, the client session
            # will not attempt to connect to the websockets server. So we only need to
            # check the case where the REST API connection succeeds but the websockets
            # connection fails.
            if client_session.rest_api.logged_in:
                await client_session.rest_api.disconnect()
            raise ClientSessionConnectionError(
                remote_host=client_session.remote_host,
                remote_port=client_session.remote_port,
                error_message=str(exc),
            ) from None
        self._logger.debug(
            f"Connected client session: {client_session!r}",
        )

        self._client_sessions[str(client_session.client_session_id)] = client_session
        self._logger.debug(
            f"Added client session: {client_session!r}",
        )

        return client_session

    # Disconnect and remove a client session by its ID.
    async def remove_client_session_by_client_session_id(
        self,
        client_session_id: str | uuid.UUID,
    ) -> None:
        client_session = self.get_client_session_by_client_session_id(
            client_session_id=client_session_id,
        )

        await client_session.disconnect()

        self._logger.debug(
            f"Disconnected client session: {client_session!r}",
        )

        removed_client_session = self._client_sessions.pop(
            str(client_session.client_session_id)
        )
        self._logger.debug(
            f"Removed client session: {removed_client_session!r}",
        )
