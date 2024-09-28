from loguru import logger

from consortium.client.client_rest_api_connection import ClientRESTAPIConnection


class ClientRESTAPIConnectionsService:
    def __init__(self):
        self._client_connections = {}
        self._client_connections_service_logger = logger.bind(
            logger_name=str(self),
        )

    def __str__(self) -> str:
        return "Client REST API Connections Service"

    def __repr__(self) -> str:
        return "ClientRESTAPIConnectionsService()"

    def add_client_connection(self, client_connection: ClientRESTAPIConnection) -> None:
        self._client_connections[str(client_connection.client_connection_id)] = (
            client_connection
        )
        self._client_connections_service_logger.debug(
            f"Added client connection: {client_connection!r}",
        )

    def get_all_client_connections(self) -> list[ClientRESTAPIConnection]:
        all_sessions = list(self._client_connections.values())
        self._client_connections_service_logger.debug(
            f"Retrieved all client connections ({len(all_sessions)} retrieved).",
        )
        return all_sessions

    def get_client_connection_by_client_connection_id(
        self,
        client_connection_id: str,
    ) -> ClientRESTAPIConnection:
        try:
            client_connection = self._client_connections[client_connection_id]
        except KeyError:
            raise ValueError(
                f"No client connection exists with the provided client connection ID: "
                f"{client_connection_id}",
            )

        self._client_connections_service_logger.debug(
            f"Retrieved client connection: {repr(client_connection)}",
        )
        return client_connection

    def remove_client_connection(
        self,
        client_connection: ClientRESTAPIConnection,
    ) -> None:
        try:
            del self._client_connections[str(client_connection.client_connection_id)]
        except KeyError:
            raise ValueError(
                f"Client session does not exist: {client_connection}",
            )

        self._client_connections_service_logger.debug(
            f"Removed client connection: {client_connection!r}",
        )
