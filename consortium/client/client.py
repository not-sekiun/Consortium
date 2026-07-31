import json
from collections import deque

import jsonschema

import consortium.client.client_config as client_config_module
import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.core_commands.banner import BannerCommand
from consortium.client.exceptions.client_session_exceptions import (
    BaseClientSessionError,
)
from consortium.client.exceptions.rest_api_exceptions import (
    RestAPIOperationError,
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
from consortium.client.models.interpreter_context_models import (
    BaseInterpreterContext,
    InteractAgentInterpreterContext,
    UseAgentTemplateInterpreterContext,
    UseListenerTemplateInterpreterContext,
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
from consortium.client.utils.printer_utils import (
    print_error,
    print_info,
    print_success,
)
from consortium.client.utils.ui_utils import with_spinner


class Client:
    def __init__(self, client_config: ClientConfig):
        self._client_sessions_service = client_singletons.client_sessions_service
        self._client_config = client_config
        self._aliases = self._load_aliases_from_aliases_json_file()
        self._resource_commands = deque()

    @property
    def _base_interpreter_context(self) -> BaseInterpreterContext:
        return BaseInterpreterContext(
            aliases=self._aliases,
            resource_commands=self._resource_commands,
        )

    @staticmethod
    def _load_aliases_from_aliases_json_file() -> dict[str, Alias]:
        aliases = {}
        with open(client_config_module.CONSORTIUM_ALIASES_JSON_FILE_PATH) as file:
            try:
                alias_json = json.load(file)
                jsonschema.validate(
                    alias_json,
                    {
                        "type": "object",
                        "properties": {
                            "local_aliases": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                            "global_aliases": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                        },
                        "additionalProperties": False,
                        "required": ["local_aliases", "global_aliases"],
                    },
                )
            except json.JSONDecodeError:
                print_error(
                    "Failed to load client aliases from "
                    f"{client_config_module.CONSORTIUM_ALIASES_JSON_FILE_PATH}. The "
                    "client alias file was not valid JSON."
                )
                return aliases
            except jsonschema.ValidationError:
                print_error(
                    "Failed to load client aliases from "
                    f"{client_config_module.CONSORTIUM_ALIASES_JSON_FILE_PATH}. The "
                    "client alias file was invalidly formatted. Hint: An entry should "
                    "be formatted as: "
                    "{'local_aliases'/'global_aliases': {<alias_1>: <command_1>, <alias_2>: <command_2>}}"
                )
                return aliases

            for alias, command in alias_json["local_aliases"].items():
                aliases[alias] = Alias(command=command, is_global=False)
            for alias, command in alias_json["global_aliases"].items():
                aliases[alias] = Alias(command=command, is_global=True)

        return aliases

    @with_spinner()
    async def _connect(self) -> ClientSession | None:
        try:
            client_session = await self._client_sessions_service.create_client_session(
                username=self._client_config.username,
                password=self._client_config.password,
                remote_host=self._client_config.remote_host,
                remote_port=self._client_config.remote_port,
            )
        except BaseClientSessionError as exc:
            print_error(
                f"Failed to login to server at "
                f"{self._client_config.remote_host}:{self._client_config.remote_port} "
                f"as '{self._client_config.username}'.",
                exc=exc,
            )
            return None

        print_success(
            f"Logged in to server at "
            f"{self._client_config.remote_host}:{self._client_config.remote_port} "
            f"as '{self._client_config.username}'.",
        )
        return client_session

    async def _display_startup_banner(
        self, client_session: ClientSession | None
    ) -> None:
        if client_session is None:
            await BannerCommand().run(
                context=DisconnectedContext(
                    command="banner",
                    arguments=[],
                    raw_input="banner",
                    interpreter_context=BaseInterpreterContext(
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                    ),
                ),
            )
        else:
            await BannerCommand().run(
                context=ConnectedContext(
                    command="banner",
                    arguments=[],
                    raw_input="banner",
                    client_session=client_session,
                    interpreter_context=BaseInterpreterContext(
                        aliases=self._aliases,
                        resource_commands=self._resource_commands,
                    ),
                ),
            )

    async def _run_disconnected_interpreter(self) -> InterpreterSignal:
        return await DisconnectedInterpreter(
            interpreter_context=BaseInterpreterContext(
                aliases=self._aliases,
                resource_commands=self._resource_commands,
            ),
        ).run()

    async def _handle_client_session(
        self,
        client_session: ClientSession,
    ) -> InterpreterSignal:
        interpreter = HomeInterpreter(
            client_session=client_session,
            interpreter_context=BaseInterpreterContext(
                aliases=self._aliases,
                resource_commands=self._resource_commands,
            ),
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
                        interpreter_context=BaseInterpreterContext(
                            aliases=self._aliases,
                            resource_commands=self._resource_commands,
                        ),
                    )
                case SwitchListenersInterpreterSignal():
                    interpreter = ListenersInterpreter(
                        client_session=client_session,
                        interpreter_context=BaseInterpreterContext(
                            aliases=self._aliases,
                            resource_commands=self._resource_commands,
                        ),
                    )
                case SwitchAgentsInterpreterSignal():
                    interpreter = AgentsInterpreter(
                        client_session=client_session,
                        interpreter_context=BaseInterpreterContext(
                            aliases=self._aliases,
                            resource_commands=self._resource_commands,
                        ),
                    )
                case SwitchGeneratorsInterpreterSignal():
                    interpreter = GeneratorsInterpreter(
                        client_session=client_session,
                        interpreter_context=BaseInterpreterContext(
                            aliases=self._aliases,
                            resource_commands=self._resource_commands,
                        ),
                    )
                case SwitchUseAgentTemplateInterpreterSignal():
                    interpreter = UseAgentTemplateInterpreter(
                        client_session=client_session,
                        interpreter_context=UseAgentTemplateInterpreterContext(
                            aliases=self._aliases,
                            resource_commands=self._resource_commands,
                            agent_template=interpreter_signal.agent_template,
                        ),
                    )
                case SwitchUseListenerTemplateInterpreterSignal():
                    interpreter = UseListenerTemplateInterpreter(
                        client_session=client_session,
                        interpreter_context=UseListenerTemplateInterpreterContext(
                            aliases=self._aliases,
                            resource_commands=self._resource_commands,
                            listener_template=interpreter_signal.listener_template,
                        ),
                    )
                case SwitchInteractAgentInterpreterSignal():
                    interpreter = InteractAgentInterpreter(
                        client_session=client_session,
                        interpreter_context=InteractAgentInterpreterContext(
                            aliases=self._aliases,
                            resource_commands=self._resource_commands,
                            agent=interpreter_signal.agent,
                        ),
                    )
                case _:
                    raise AssertionError(
                        "Failed to handle return signal from interpreter. The return "
                        f"signal '{interpreter_signal}' is not supported."
                    )

    async def run(self) -> None:
        client_session = await self._connect()
        await self._display_startup_banner(client_session=client_session)

        # Run the initial interpreter. Either we run a special disconnected interpreter
        # that can run independently of any client session in the case where a
        # connection failed, or we run the client session's own interpreter loop for a
        # successful initial connection.
        if client_session is None:
            interpreter_signal = await self._run_disconnected_interpreter()
        else:
            interpreter_signal = await self._handle_client_session(
                client_session=client_session,
            )

        # Based on successive client session return statuses decide whether to continue
        # running client sessions or not.
        while True:
            match interpreter_signal:
                case ExitClientSignal():
                    return
                case ExitClientSessionSignal():
                    interpreter_signal = await self._run_disconnected_interpreter()
                case SwitchClientSessionSignal() as previous_interpreter_signal:
                    try:
                        # The client connection switched to has no guarantee of being
                        # valid
                        interpreter_signal = await self._handle_client_session(
                            client_session=previous_interpreter_signal.client_session
                        )
                    except RestAPIOperationError as exc:
                        print_error(
                            f"Failed to switch to client session "
                            f"{previous_interpreter_signal.client_session}.",
                            exc=exc,
                        )
                        print_info(
                            "Switching to disconnected interpreter due to error raised "
                            + "while switching client sessions..."
                        )
                        interpreter_signal = await self._run_disconnected_interpreter()
                    # # Catch any fatal errors raised by the client session. If a fatal error
                    # # occurs in any of the interpreters it is already printed. We catch it
                    # # here and kill the session.
                    # except Exception as exc:
                    #     print_error(
                    #         f"Unhandled exception occurred while switching to client "
                    #         f"session {return_status.data['client_session']}.",
                    #         exc=exc
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
