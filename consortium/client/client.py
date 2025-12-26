from aiohttp.client import ClientConnectionError
from websockets.exceptions import WebSocketException

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.core_commands.banner import BannerCommand
from consortium.client.exceptions.rest_api_exceptions import (
    RestApiAuthenticationError,
)
from consortium.client.exceptions.websockets_api_exceptions import (
    WebsocketsApiConnectionError,
)
from consortium.client.interpreters import (
    AgentsInterpreter,
    GeneratorsInterpreter,
    HomeInterpreter,
    InteractAgentInterpreter,
    ListenersInterpreter,
    UseAgentTemplateInterpreter,
    UseListenerTemplateInterpreter,
)
from consortium.client.interpreters.disconnected_interpreter import (
    DisconnectedInterpreter,
)
from consortium.client.models.client_models import ClientConfig
from consortium.client.models.return_status_models import (
    InterpreterType,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import Context
from consortium.client.utils.printer_utils import print_error, print_success


class Client:
    def __init__(self, client_config: ClientConfig):
        self._client_sessions_service = client_singletons.client_sessions_service
        self._client_config = client_config

    @staticmethod
    async def _handle_client_session_interpreters(client_session: ClientSession):
        interpreter = HomeInterpreter(client_session=client_session)

        while True:
            return_status = await interpreter.run()
            if return_status.type in (
                ReturnStatusType.EXIT_CLIENT,
                ReturnStatusType.EXIT_CLIENT_SESSION,
                ReturnStatusType.SWITCH_CLIENT_SESSION,
            ):
                return return_status
            elif return_status.type == ReturnStatusType.SWITCH_INTERPRETER:
                interpreter_type = return_status.data["interpreter_type"]
                if interpreter_type == InterpreterType.HOME_INTERPRETER:
                    interpreter = HomeInterpreter(client_session=client_session)
                elif interpreter_type == InterpreterType.LISTENERS_INTERPRETER:
                    interpreter = ListenersInterpreter(client_session=client_session)
                elif interpreter_type == InterpreterType.AGENTS_INTERPRETER:
                    interpreter = AgentsInterpreter(client_session=client_session)
                elif interpreter_type == InterpreterType.GENERATORS_INTERPRETER:
                    interpreter = GeneratorsInterpreter(client_session=client_session)
                elif interpreter_type == InterpreterType.USE_AGENT_TEMPLATE_INTERPRETER:
                    interpreter = UseAgentTemplateInterpreter(
                        client_session=client_session,
                        agent_template=return_status.data["agent_template"],
                    )
                elif (
                    interpreter_type
                    == InterpreterType.USE_LISTENER_TEMPLATE_INTERPRETER
                ):
                    interpreter = UseListenerTemplateInterpreter(
                        client_session=client_session,
                        listener_template=return_status.data["listener_template"],
                    )
                elif interpreter_type == InterpreterType.INTERACT_AGENT_INTERPRETER:
                    interpreter = InteractAgentInterpreter(
                        client_session=client_session,
                        agent=return_status.data["agent"],
                    )
                else:
                    raise AssertionError(
                        "Failed to switch to interpreter with interpreter type "
                        f"'{interpreter_type}'. Invalid interpreter type was returned "
                        "as part of the return status."
                    )

    async def run(self):
        try:
            client_session = ClientSession(
                username=self._client_config.username,
                password=self._client_config.password,
                remote_host=self._client_config.remote_host,
                remote_port=self._client_config.remote_port,
            )
            await client_session.connect()
            rest_api = client_session.rest_api
            websockets_api = client_session.websockets_api
            print_success(
                f"Successfully logged into server: "
                f"{self._client_config.remote_host}:{self._client_config.remote_port} "
                f"as '{self._client_config.username}'.",
            )
        except (
            # Exceptions raised when failing to log in to the REST API.
            RestApiAuthenticationError,
            ClientConnectionError,
            # Exceptions raised when failing to connect to the Websockets API.
            WebsocketsApiConnectionError,
            WebSocketException,
            # Generic exceptions that can occur during network communication.
            TimeoutError,
            OSError,
        ) as exc:
            client_session = None
            rest_api = None
            websockets_api = None
            print_error(
                f"Failed to login to server. An error occurred while attempting to "
                f"login to the server: {exc}",
            )

        # Display banner once at client startup.
        await BannerCommand().run(
            context=Context(
                command="banner",
                arguments=[],
                raw_input="banner",
                client_session=client_session,
                interpreter_context=None,
                # The banner command needs the client session, client REST API
                # connection and client websockets API connections as part of its
                # environment to display relevant information. If those values are
                # passed as `None` to it, the banner command recognizes that it is
                # (or will be) running in the context of a disconnected interpreter.
                environment={
                    "client_session": client_session,
                    "rest_api": rest_api,
                    "websockets_api": websockets_api,
                },
            ),
        )

        # Run the initial interpreter. Either we run a special disconnected interpreter
        # that can run independently of any client session in the case where a
        # connection failed, or we run the client session's own interpreter loop for a
        # successful initial connection.
        if client_session is None:
            return_status = await DisconnectedInterpreter().run()
        else:
            self._client_sessions_service.add_client_session(
                client_session=client_session
            )
            return_status = await self._handle_client_session_interpreters(
                client_session=client_session,
            )

        # Based on successive client session return statuses decide whether to continue
        # running client sessions or not.
        while True:
            # ReturnStatusType.SWITCH_INTERPRETER will never be returned since the
            # client session itself will handle that return status type.
            if return_status.type == ReturnStatusType.EXIT_CLIENT:
                return
            elif return_status.type == ReturnStatusType.EXIT_CLIENT_SESSION:
                return_status = await DisconnectedInterpreter().run()
            elif return_status.type == ReturnStatusType.SWITCH_CLIENT_SESSION:
                try:
                    # The client connection switched to has no guarantee of being valid
                    return_status = await self._handle_client_session_interpreters(
                        client_session=return_status.data["client_session"]
                    )
                # Catch any fatal errors raised by the client session. If a fatal error
                # occurs in any of the interpreters it is already printed and the error
                # reraised. We catch it here and kill the session.
                except Exception:
                    self._client_sessions_service.client_sessions_service.remove_client_session_by_client_session_id(
                        client_session_id=return_status.data[
                            "client_session"
                        ].client_session_id,
                    )
                    return_status = await DisconnectedInterpreter().run()
            else:
                raise AssertionError(
                    "Failed to handle return status from interpreter. The return "
                    f"status type '{return_status.type}' is not supported."
                )
