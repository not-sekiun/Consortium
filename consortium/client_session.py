import uuid

from consortium.client.client_connection import ClientConnection


class ClientSession:
    def __init__(self, client_connection: ClientConnection):
        self.client_connection = client_connection

        self.name = ""
        self.username = client_connection.client_config.username
        self.password = client_connection.client_config.password
        self.remote_host = client_connection.client_config.remote_host
        self.remote_port = client_connection.client_config.remote_port
        self.datetime_connected = client_connection.datetime_connected
        self.client_session_id = uuid.uuid4()
