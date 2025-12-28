from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

import consortium.client.client_singletons as client_singletons
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.disconnected_interpreter_commands import (
    DISCONNECTED_INTERPRETER_COMMANDS,
)
from consortium.client.commands.home_interpreter_commands import (
    ClientSessionListCommand,
    ConnectCommand,
    InteractClientSessionCommand,
)
from consortium.client.repl_interface.interpreter import Interpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

client_sessions_service = client_singletons.client_sessions_service


class DisconnectedInterpreter(Interpreter):
    def __init__(self):
        combined_disconnected_interpreter_core_commands = (
            [
                command
                for command in CORE_COMMANDS
                if command.name not in ("home", "listeners", "generators", "agents")
            ]
            + DISCONNECTED_INTERPRETER_COMMANDS
            + [
                ConnectCommand(),
                ClientSessionListCommand(),
                InteractClientSessionCommand(),
            ]
        )
        super().__init__(
            prompt=ANSI(format_rich_text_as_ansi("[bold white]Consortium\n> ")),
            commands=[
                *combined_disconnected_interpreter_core_commands,
            ],
            client_session=None,
        )

    async def on_loop(self) -> None:
        all_client_sessions = client_sessions_service.get_all_client_sessions()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            nested_completer=self.prompt_session.completer,
        )
        for key, value in {
            command: {
                str(client_session.client_session_id): None
                for client_session in all_client_sessions
            }
            for command in [
                "disconnect",
                "info",
                "interact",
                "rename",
                "describe",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = dict.fromkeys(self.commands)

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
