from loguru import logger

from consortium.client.client_session import ClientSession


class ClientSessionsService:
    def __init__(self):
        self._client_sessions = {}
        self._client_sessions_service_logger = logger.bind(
            logger_name="Consortium Session Service",
        )

    def add_client_session(self, client_session: ClientSession) -> None:
        self._client_sessions[str(client_session.client_session_id)] = client_session
        self._client_sessions_service_logger.debug(
            f"Added client session: {client_session!r}",
        )

    def get_all_client_sessions(self) -> list[ClientSession]:
        all_sessions = list(self._client_sessions.values())
        self._client_sessions_service_logger.debug(
            f"Retrieved all client sessions ({len(all_sessions)} retrieved).",
        )
        return all_sessions

    def get_client_session_by_client_session_id(
        self,
        client_session_id: str,
    ) -> ClientSession:
        try:
            client_session = self._client_sessions[client_session_id]
        except KeyError:
            raise ValueError(
                f"No client session exists with the provided client session ID: {client_session_id}",
            )

        self._client_sessions_service_logger.debug(
            f"Retrieved client session: {repr(client_session)}",
        )
        return client_session

    def remove_client_session(self, client_session: ClientSession) -> None:
        try:
            del self._client_sessions[str(client_session.client_session_id)]
        except KeyError:
            raise ValueError(
                f"Client session does not exist: {client_session}",
            )

        self._client_sessions_service_logger.debug(
            f"Removed client session: {client_session!r}",
        )
