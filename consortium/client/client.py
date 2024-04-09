from consortium.client.client_connection import ClientConnection
from consortium.client.client_exceptions import (
    AlreadyLoggedInError,
    FailedToLoginError,
    InvalidServerLoginResponseError,
)
from consortium.client.client_session import ClientSession
from consortium.client.objects.client_objects import ClientConfig


class Client:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

    async def start_client(self):
        client_connection = ClientConnection(client_config=self.client_config)
        try:
            await client_connection.login()
        # AlreadyLoggedInError should not be raised unless a programmer error is made.
        except (
            FailedToLoginError,
            InvalidServerLoginResponseError,
            AlreadyLoggedInError,
        ) as exc:
            print(exc)

        await ClientSession(client_connection=client_connection).run_client_session()
