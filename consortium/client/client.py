from aiohttp.client import ClientConnectionError

import consortium.client.client_singletons as client_singletons
from consortium.client.client_rest_api_connection import ClientRESTAPIConnection
from consortium.client.client_session import ClientSession
from consortium.client.commands.core_commands.banner import BannerCommand
from consortium.client.exceptions.client_rest_api_connection_exceptions import (
    ClientRESTAPIConnectionAlreadyLoggedInError,
    ClientRESTAPIConnectionFailedToLoginError,
    InvalidServerRESTAPILoginResponseError,
)
from consortium.client.framework.base_command import CommandContext
from consortium.client.interpreters.disconnected_interpreter import (
    DisconnectedInterpreter,
)
from consortium.client.objects.client_objects import ClientConfig
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import print_error, print_success

client_connections_service = client_singletons.client_connections_service


class Client:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

    async def start_client(self):
        client_connection = ClientRESTAPIConnection(client_config=self.client_config)

        try:
            await client_connection.login()
            print_success(
                f"Logged into server: "
                f"{self.client_config.remote_host}:{self.client_config.remote_port}",
            )
        # AlreadyLoggedInError should not be raised unless a programmer error is made.
        except (
            ClientRESTAPIConnectionFailedToLoginError,
            InvalidServerRESTAPILoginResponseError,
            ClientRESTAPIConnectionAlreadyLoggedInError,
            ClientConnectionError,
        ) as exc:
            print_error(f"Failed to login to server: {exc}")
            client_connection = None

        # Display banner once at client startup.
        banner_command = BannerCommand()
        await banner_command.run_command(
            command_context=CommandContext(
                command="banner",
                arguments=[],
                original_string="banner",
                environment={"client_connection": client_connection},
            ),
        )

        # Get the first client session return status regardless of whether a client
        # connection was established or not
        if client_connection:
            client_connections_service.add_client_connection(client_connection)
            return_status = await ClientSession(
                client_connection=client_connection,
            ).run_client_session()
        else:
            # Disconnected interpreter returns a return status telling us whether to
            # exit the program or switch to a newly established client connection.
            return_status = await DisconnectedInterpreter().run_interpreter()

        # Based on successive client session return statuses decide whether to continue
        # running client sessions or not.
        while True:
            # ClientReturnStatusType.SWITCH_INTERPRETER will never be returned since the
            # client session itself will handle that return status type.
            if return_status.type == ClientReturnStatusType.EXIT:
                return
            elif return_status.type == ClientReturnStatusType.EXIT_CLIENT_CONNECTION:
                return_status = await DisconnectedInterpreter().run_interpreter()
            elif return_status.type == ClientReturnStatusType.SWITCH_CLIENT_CONNECTION:
                # The command will make sure that the client connection is valid.
                return_status = await ClientSession(
                    client_connection=return_status.data["client_connection"],
                ).run_client_session()
