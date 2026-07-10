class ClientSessionNotFoundError(Exception):
    def __init__(self, client_session_id: str):
        super().__init__(
            "Failed to find the requested client session. No client session was found "
            f"with the provided client session ID '{client_session_id}'",
        )


class ClientSessionAlreadyExistsError(Exception):
    def __init__(self, client_session_id: str):
        super().__init__(
            "Failed to add the provided client session. A client session already "
            f"exists with the provided client session ID '{client_session_id}'",
        )


class ClientSessionConnectionError(Exception):
    def __init__(self, remote_host: str, remote_port: int, error_message: str):
        super().__init__(
            "Failed to create new client session. An error occurred while attempting "
            f"to connect to the server {remote_host}:{remote_port}. {error_message}",
        )
