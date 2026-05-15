import json
from collections import deque

import jsonschema
from aiohttp.client import ClientConnectionError
from websockets.exceptions import WebSocketException

import consortium.client.client_config as client_config_module
import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.core_commands.banner import BannerCommand
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionConnectionError,
)
from consortium.client.exceptions.rest_api_exceptions import (
    RestAPIError,
    RestAPIOperationError,
)
from consortium.client.exceptions.websockets_api_exceptions import (
    WebsocketsAPIError,
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
from consortium.client.models.alias_model import Alias
from consortium.client.models.client_models import ClientConfig
from consortium.client.models.context_models import (
    ConnectedContext,
    DisconnectedContext,
)
from consortium.client.models.interpreter_signal_models import (
    ExitClientSessionSignal,
    ExitClientSignal,
    InterpreterSignal,
    SwitchAgentsInterpreterSignal,
    SwitchClientSessionSignal,
    SwitchGeneratorsInterpreterSignal,
    SwitchHomeInterpreterSignal,
    SwitchInteractAgentInterpreterSignal,
    SwitchListenersInterpreterSignal,
    SwitchUseAgentTemplateInterpreterSignal,
    SwitchUseListenerTemplateInterpreterSignal,
)
from consortium.client.utils.printer_utils import print_error, print_info, print_success


class Client:
    def __init__(self, client_config: ClientConfig):
        self._client_sessions_service = client_singletons.client_sessions_service
        self._client_config = client_config
        self._aliases = {}
        with open(client_config_module.CONSORTIUM_ALIASES_JSON_FILE_PATH) as file:
            alias_json = json.load(file)
            jsonschema.validate(
                alias_json,
                {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "is_global": {"type": "boolean"},
                        },
                        "required": ["command", "is_global"],
                        "additionalProperties": False,
                    },
                },
            )
            for alias_name, alias in alias_json.items():
                self._aliases[alias_name] = Alias(
                    command=alias["command"], is_global=alias["is_global"]
                )
        self._resource_commands = deque()

    async def _handle_client_session_interpreters(
        self,
        client_session: ClientSession,
    ) -> InterpreterSignal:
        interpreter = HomeInterpreter(
            client_session=client_session,
            aliases=self._aliases,
            resource_commands=self._resource_commands,
        )

        while True:
            interpreter_signal = await interpreter.run()

            match interpreter_signal:
                case (
                    ExitClientSignal()
                    | ExitClientSessionSignal()
                    | SwitchClientSessionSignal()
                ):
                    return interpreter_signal
                case SwitchHomeInterpreterSignal():
                    interpreter = HomeInterpreter(
                        client_session=client_session,
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                    )
                case SwitchListenersInterpreterSignal():
                    interpreter = ListenersInterpreter(
                        client_session=client_session,
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                    )
                case SwitchAgentsInterpreterSignal():
                    interpreter = AgentsInterpreter(
                        client_session=client_session,
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                    )
                case SwitchGeneratorsInterpreterSignal():
                    interpreter = GeneratorsInterpreter(
                        client_session=client_session,
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                    )
                case SwitchUseAgentTemplateInterpreterSignal():
                    interpreter = UseAgentTemplateInterpreter(
                        client_session=client_session,
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                        agent_template=interpreter_signal.agent_template,
                    )
                case SwitchUseListenerTemplateInterpreterSignal():
                    interpreter = UseListenerTemplateInterpreter(
                        client_session=client_session,
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                        listener_template=interpreter_signal.listener_template,
                    )
                case SwitchInteractAgentInterpreterSignal():
                    interpreter = InteractAgentInterpreter(
                        client_session=client_session,
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                        agent=interpreter_signal.agent,
                    )
                case _:
                    raise AssertionError(
                        "Failed to handle return signal from interpreter. The return "
                        f"signal '{interpreter_signal}' is not supported."
                    )

    async def run(self) -> None:
        try:
            client_session = await self._client_sessions_service.create_client_session(
                username=self._client_config.username,
                password=self._client_config.password,
                remote_host=self._client_config.remote_host,
                remote_port=self._client_config.remote_port,
            )
            print_success(
                f"Connected to server "
                f"{self._client_config.remote_host}:{self._client_config.remote_port} "
                f"as '{self._client_config.username}'.",
            )
        except (
            # Exceptions raised when failing to log in to the REST API.
            RestAPIError,
            # Exceptions raised when failing to connect to the Websockets API.
            WebsocketsAPIError,
            # Generic network exceptions.
            ClientSessionConnectionError,
            WebSocketException,
            ClientConnectionError,
            TimeoutError,
            OSError,
        ) as exc:
            client_session = None
            print_error(
                f"Failed to connect to server "
                f"{self._client_config.remote_host}:{self._client_config.remote_port}. "
                f"An error occurred while attempting to login. "
                f"{exc.__class__.__name__}: {exc}",
            )

        # Run the initial interpreter. Either we run a special disconnected interpreter
        # that can run independently of any client session in the case where a
        # connection failed, or we run the client session's own interpreter loop for a
        # successful initial connection.
        if client_session is None:
            # Display banner once at client startup.
            await BannerCommand().run(
                context=DisconnectedContext(
                    command="banner",
                    arguments=[],
                    raw_input="banner",
                    interpreter_context={},
                ),
            )
            interpreter_signal = await DisconnectedInterpreter(
                aliases=self._aliases,
                resource_commands=self._resource_commands,
            ).run()
        else:
            # Display banner once at client startup.
            await BannerCommand().run(
                context=ConnectedContext(
                    command="banner",
                    arguments=[],
                    raw_input="banner",
                    client_session=client_session,
                    interpreter_context={},
                ),
            )
            interpreter_signal = await self._handle_client_session_interpreters(
                client_session=client_session,
            )

        # Based on successive client session return statuses decide whether to continue
        # running client sessions or not.
        while True:
            match interpreter_signal:
                case ExitClientSignal():
                    return
                case ExitClientSessionSignal():
                    interpreter_signal = await DisconnectedInterpreter(
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                    ).run()
                case SwitchClientSessionSignal() as previous_interpreter_signal:
                    try:
                        # The client connection switched to has no guarantee of being valid
                        interpreter_signal = await self._handle_client_session_interpreters(
                            client_session=previous_interpreter_signal.client_session
                        )
                    except RestAPIOperationError as exc:
                        print_error(
                            f"Failed to switch to client session "
                            f"{previous_interpreter_signal.client_session}. {exc}",
                        )
                        print_info(
                            "Switching to disconnected interpreter due to error raised "
                            + "while switching client sessions..."
                        )
                        interpreter_signal = await DisconnectedInterpreter(
                            aliases=self._aliases,
                            resource_commands=self._resource_commands,
                        ).run()
                    # # Catch any fatal errors raised by the client session. If a fatal error
                    # # occurs in any of the interpreters it is already printed. We catch it
                    # # here and kill the session.
                    # except Exception as exc:
                    #     print_error(
                    #         f"Unhandled exception occurred while switching to client "
                    #         f"session {return_status.data['client_session']}. "
                    #         f"{exc.__class__.__name__}: {exc}"
                    #     )
                    #     console.print_exception(show_locals=True)
                    #     print_info("Removing the faulty client session...")
                    #     self._client_sessions_service.remove_client_session_by_client_session_id(
                    #         client_session_id=return_status.data[
                    #             "client_session"
                    #         ].client_session_id,
                    #     )
                    #     return_status = await DisconnectedInterpreter().run()
                case _:
                    raise AssertionError(
                        "Failed to handle return signal from interpreter. The return "
                        f"signal '{interpreter_signal}' is not supported."
                    )
