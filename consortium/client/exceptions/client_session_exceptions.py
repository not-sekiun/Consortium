class ClientSessionAlreadyConnectedException(Exception):
    def __init__(self):
        super().__init__(
            "Failed to connect client session. Client session is already connected to "
            "a server.",
        )


class ClientSessionNotConnectedException(Exception):
    def __init__(self):
        super().__init__(
            "Failed to disconnect client session. Client session is not connected to "
            "any server.",
        )
