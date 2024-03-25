import uuid


class Session:
    def __init__(
        self,
        username: str,
        password: str,
        remote_host: str,
        remote_port: int,
    ):
        self.username = username
        self.password = password
        self.remote_host = remote_host
        self.remote_port = remote_port

        self.session_id = uuid.uuid4()
