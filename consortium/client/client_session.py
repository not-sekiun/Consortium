import uuid

from consortium.client.client_connection import ClientConnection


class ClientSession:
    def __init__(self, client_connection: ClientConnection):
        self.client_connection = client_connection

        self.name = ""
        self.client_session_id = uuid.uuid4()

    async def run_client_session(self):
        print(await self.client_connection.get_server_release())
        await self.client_connection.logout()
        await self.client_connection.close()
