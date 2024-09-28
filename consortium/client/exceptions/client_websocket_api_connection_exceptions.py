class ClientWebsocketsAPIConnectionAuthenticationError(Exception):
    pass


class ClientWebsocketsAPIConnectionAlreadyConnectedError(
    ClientWebsocketsAPIConnectionAuthenticationError,
):
    def __init__(self):
        super().__init__(
            "Failed to connect to the server's websockets API. Client is already "
            "connected to the server over its websockets API (Disconnect from the "
            "server before attempting to reconnect).",
        )


class ClientWebsocketsAPIConnectionNotConnectedError(
    ClientWebsocketsAPIConnectionAuthenticationError,
):
    super().__init__(
        "Failed to perform the requested operation over the server's websockets API. "
        "Client is not connected to the server over its websockets API.",
    )


class ClientWebsocketsAPIConnectionFailedToConnectError(
    ClientWebsocketsAPIConnectionAuthenticationError,
):
    def __init__(self):
        super().__init__(
            "Failed to connect to the server over its websockets API. Either invalid "
            "credentials were provided or the server is not a valid Consortium "
            "server instance.",
        )


class ClientWebsocketAPIConnectionOperationError(Exception):
    pass


class InvalidServerWebsocketAPIConnectionResponseError(
    ClientWebsocketAPIConnectionOperationError,
):
    def __init__(self):
        super().__init__(
            "Failed to perform the requested operation over the server's websockets "
            "API. Server did not return a valid response. The server is likely not a "
            "valid Consortium server instance.",
        )


class SeverWebsocketAPIErrorResponseError(ClientWebsocketAPIConnectionOperationError):
    def __init__(self, error_message: str):
        super().__init__(
            "Failed to perform the requested operation over the server's websockets "
            f"API. Server returned the following error response: {error_message}",
        )
