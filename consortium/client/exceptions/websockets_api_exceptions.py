class WebsocketsAPIError(Exception): ...


class WebsocketsAPIConnectionError(WebsocketsAPIError): ...


class WebsocketsAPIAlreadyConnectedError(WebsocketsAPIConnectionError):
    def __init__(self):
        super().__init__(
            "Failed to connect to the server's websockets API. Client is already "
            "connected to the server over its websockets API (Disconnect from the "
            "server before attempting to reconnect).",
        )


class WebsocketsAPINotConnectedError(WebsocketsAPIConnectionError):
    def __init__(self):
        super().__init__(
            "Failed to perform the requested operation over the server's websockets API. "
            "Client is not connected to the server over its websockets API.",
        )


class WebsocketsAPIFailedToConnectError(WebsocketsAPIConnectionError):
    def __init__(self):
        super().__init__(
            "Failed to connect to the server over its websockets API. Either invalid "
            "credentials were provided or the server is not a valid Consortium "
            "server instance.",
        )


class InvalidServerWebsocketAPIResponseError(WebsocketsAPIError):
    def __init__(self):
        super().__init__(
            "Failed to perform the requested operation over the server's websockets "
            "API. Server did not return a valid response. The server is likely not a "
            "valid Consortium server instance.",
        )


class SeverWebsocketsAPIErrorResponseError(WebsocketsAPIError):
    def __init__(self, error_message: str):
        super().__init__(
            "Failed to perform the requested operation over the server's websockets "
            f"API. Server returned the following error response: {error_message}",
        )


class WebsocketsAPIHandlerAlreadyRunningError(WebsocketsAPIError):
    def __init__(self):
        super().__init__(
            "Failed to start the websockets API handler. The handler is already running.",
        )


class WebsocketsAPIHandlerNotRunningError(WebsocketsAPIError):
    def __init__(self):
        super().__init__(
            "Failed to stop the websockets API handler. The handler is not running.",
        )


class InvalidEventTypeError(Exception):
    def __init__(self, event_type: str):
        super().__init__(
            "Failed to perform the requested operation. Invalid event type "
            f"'{event_type}' was provided.",
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
