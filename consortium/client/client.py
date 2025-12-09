from aiohttp.client import ClientConnectionError
from websockets.exceptions import WebSocketException

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.core_commands.banner import BannerCommand
from consortium.client.exceptions.client_rest_api_connection_exceptions import (
    ClientRESTAPIAuthenticationError,
)
from consortium.client.exceptions.client_websocket_api_connection_exceptions import (
    ClientWebsocketsAPIConnectionError,
)
from consortium.client.interpreters.disconnected_interpreter import (
    DisconnectedInterpreter,
)
from consortium.client.objects.client_objects import ClientConfig
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext
from consortium.client.utils.printer_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class Client:
    def __init__(self, client_config: ClientConfig):
        self._client_config = client_config

    async def start(self):
        try:
            client_session = ClientSession(
                username=self._client_config.username,
                password=self._client_config.password,
                remote_host=self._client_config.remote_host,
                remote_port=self._client_config.remote_port,
            )
            await client_session.connect()
            client_rest_api_connection = client_session.client_rest_api_connection
            client_websockets_api_connection = (
                client_session.client_websockets_api_connection
            )
            print_success(
                f"Successfully logged into server: "
                f"{self._client_config.remote_host}:{self._client_config.remote_port} "
                f"as '{self._client_config.username}'.",
            )
        except (
            # Exceptions raised when failing to log in to the REST API.
            ClientRESTAPIAuthenticationError,
            ClientConnectionError,
            # Exceptions raised when failing to connect to the Websockets API.
            ClientWebsocketsAPIConnectionError,
            WebSocketException,
            TimeoutError,
            OSError,
        ) as exc:
            client_session = None
            client_rest_api_connection = None
            client_websockets_api_connection = None
            print_error(
                f"Failed to login to server. An error occurred while attempting to "
                f"login to the server: {exc}",
            )

        # Display banner once at client startup.
        await BannerCommand().run_command(
            command_context=CommandContext(
                command="banner",
                arguments=[],
                original_string="banner",
                # The banner command needs the client session, client REST API
                # connection and client websockets API connections as part of its
                # environment to display relevant information. If those values are
                # passed as `None` to it, the banner command recognizes that it is
                # (or will be) running in the context of a disconnected interpreter.
                environment={
                    "client_session": client_session,
                    "client_rest_api_connection": client_rest_api_connection,
                    "client_websockets_api_connection": client_websockets_api_connection,
                },
            ),
        )

        # Run the initial interpreter. Either we run a special disconnected interpreter
        # that can run independently of any client session in the case where a
        # connection failed, or we run the client session's own interpreter loop for a
        # successful initial connection.
        if client_session is None:
            return_status = await DisconnectedInterpreter().run_interpreter()
        else:
            client_sessions_service.add_client_session(client_session=client_session)
            return_status = await client_session.run()

        # Based on successive client session return statuses decide whether to continue
        # running client sessions or not.
        while True:
            # ClientReturnStatusType.SWITCH_INTERPRETER will never be returned since the
            # client session itself will handle that return status type.
            if return_status.type == ClientReturnStatusType.EXIT:
                return
            elif return_status.type == ClientReturnStatusType.EXIT_CLIENT_SESSION:
                return_status = await DisconnectedInterpreter().run_interpreter()
            elif return_status.type == ClientReturnStatusType.SWITCH_CLIENT_SESSION:
                try:
                    # The command will make sure that the client connection is valid.
                    return_status = await return_status.data["client_session"].run()
                # Catch any fatal errors raised by the client session. If a fatal error
                # occurs in any of the interpreters it is already printed and the error
                # reraised. We catch it here and kill the session.
                except Exception:
                    client_sessions_service.remove_client_session_by_client_session_id(
                        client_session_id=return_status.data[
                            "client_session"
                        ].client_session_id,
                    )
                    return_status = await DisconnectedInterpreter().run_interpreter()
            else:
                raise AssertionError(
                    "Failed to handle return status from interpreter. The return "
                    f"status type '{return_status.type}' is not supported."
                )
