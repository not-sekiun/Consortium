class ClientWebsocketsAPIConnectionError(Exception):
    pass


class ClientWebsocketsAPIConnectionAlreadyConnectedError(
    ClientWebsocketsAPIConnectionError,
):
    def __init__(self):
        super().__init__(
            "Failed to connect to the server's websockets API. Client is already "
            "connected to the server over its websockets API (Disconnect from the "
            "server before attempting to reconnect).",
        )


class ClientWebsocketsAPIConnectionNotConnectedError(
    ClientWebsocketsAPIConnectionError,
):
    def __init__(self):
        super().__init__(
            "Failed to perform the requested operation over the server's websockets API. "
            "Client is not connected to the server over its websockets API.",
        )


class ClientWebsocketsAPIConnectionFailedToConnectError(
    ClientWebsocketsAPIConnectionError,
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


class SeverWebsocketsAPIErrorResponseError(ClientWebsocketAPIConnectionOperationError):
    def __init__(self, error_message: str):
        super().__init__(
            "Failed to perform the requested operation over the server's websockets "
            f"API. Server returned the following error response: {error_message}",
        )


class ClientWebsocketsAPIConnectionAlreadyRunningError(
    ClientWebsocketsAPIConnectionError,
):
    def __init__(self):
        super().__init__(
            "Failed to start the server's websockets API connection. The client "
            "websockets API connection is connected to the server and already running.",
        )


class ClientWebsocketsAPIConnectionNotRunningError(
    ClientWebsocketsAPIConnectionError,
):
    def __init__(self):
        super().__init__(
            "Failed to stop the server's websockets API connection. The client "
            "websockets API connection is connected to the server but not running",
        )


class InvalidEventTypeError(Exception):
    def __init__(self, event_type: str):
        super().__init__(
            "Failed to perform the requested operation. Invalid event type "
            f"'{event_type}' was provided that does not exist.",
        )


class EventHandlerNotSubscribedError(Exception):
    def __init__(self, event_type: str):
        super().__init__(
            "Failed to unsubscribe from the requested event. The provided event "
            f"handler was not registered for event type '{event_type}'.",
        )


class EventTypeNotSubscribedError(Exception):
    def __init__(self, event_type: str):
        super().__init__(
            "Failed to unsubscribe from the requested event. The provided event type "
            f"'{event_type}' is not subscribed to by any event handlers at all.",
        )
