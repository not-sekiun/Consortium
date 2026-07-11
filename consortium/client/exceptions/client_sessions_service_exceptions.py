from consortium.client.exceptions.base_client_exception import BaseClientError


class BaseClientSessionServiceError(BaseClientError):
    pass


class ClientSessionNotFoundError(BaseClientSessionServiceError):
    def __init__(self, client_session_id: str):
        super().__init__(
            "Failed to find the requested client session. No client session was found "
            f"with the provided client session ID '{client_session_id}'",
        )


class ClientSessionAlreadyExistsError(BaseClientSessionServiceError):
    def __init__(self, client_session_id: str):
        super().__init__(
            "Failed to add the provided client session. A client session already "
            f"exists with the provided client session ID '{client_session_id}'",
        )
