from loguru import logger

from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionAlreadyExistsError,
    ClientSessionNotFoundError,
)


class ClientSessionsService:
    def __init__(self):
        self._client_sessions = {}
        self._client_sessions_service_logger = logger.bind(
            logger_name=str(self),
        )

    def __str__(self) -> str:
        return "Client Sessions Service"

    def __repr__(self) -> str:
        return "ClientSessionsService()"

    def get_all_client_sessions(self) -> list["ClientSession"]:
        all_client_sessions = list(self._client_sessions.values())
        self._client_sessions_service_logger.debug(
            f"Retrieved all client sessions ({len(all_client_sessions)} retrieved).",
        )
        return all_client_sessions

    def get_client_session_by_client_session_id(
        self,
        client_session_id: str,
    ) -> "ClientSession":
        try:
            client_session = self._client_sessions[client_session_id]
        except KeyError:
            raise ClientSessionNotFoundError(client_session_id=client_session_id)

        self._client_sessions_service_logger.debug(
            f"Retrieved client session: {repr(client_session)}",
        )
        return client_session

    def create_client_session(
        self,
        username: str,
        password: str,
        remote_host: str,
        remote_port: int,
    ) -> "ClientSession":
        # Importing here to avoid circular imports.
        from consortium.client.client_session import ClientSession

        client_session = ClientSession(
            username=username,
            password=password,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        self._client_sessions_service_logger.debug(
            f"Created client session: {client_session!r}",
        )
        return client_session

    async def connect_client_session(self, client_session_id: str) -> None:
        client_session = self.get_client_session_by_client_session_id(
            client_session_id=client_session_id,
        )
        await client_session.connect()
        self._client_sessions_service_logger.debug(
            f"Connected client session: {client_session!r}",
        )

    async def disconnect_client_session(self, client_session_id: str) -> None:
        client_session = self.get_client_session_by_client_session_id(
            client_session_id=client_session_id,
        )
        await client_session.disconnect()
        self._client_sessions_service_logger.debug(
            f"Disconnected client session: {client_session!r}",
        )

    def add_client_session(self, client_session: "ClientSession") -> None:
        if client_session.client_session_id in self._client_sessions:
            raise ClientSessionAlreadyExistsError

        self._client_sessions[str(client_session.client_session_id)] = client_session
        self._client_sessions_service_logger.debug(
            f"Added client session: {client_session!r}",
        )

    def create_and_add_client_session(
        self,
        username: str,
        password: str,
        remote_host: str,
        remote_port: int,
    ) -> "ClientSession":
        client_session = self.create_client_session(
            username=username,
            password=password,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        self.add_client_session(client_session)
        return client_session

    def remove_client_session_by_client_session_id(
        self,
        client_session_id: str,
    ) -> None:
        if client_session_id not in self._client_sessions:
            raise ClientSessionNotFoundError(client_session_id=client_session_id)

        removed_client_session = self._client_sessions.pop(client_session_id)

        self._client_sessions_service_logger.debug(
            f"Removed client session: {removed_client_session!r}",
        )
