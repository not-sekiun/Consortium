from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter

from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.commands.disconnected_interpreter_commands.disconnect import (
    DisconnectCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.info_client_connection import (
    InfoClientConnectionCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.rename_client_connection import (
    RenameClientConnectionCommand,
)
from consortium.client.commands.home_interpreter_commands.connect import ConnectCommand
from consortium.client.commands.home_interpreter_commands.interact_client_connection import (
    InteractClientConnectionCommand,
)
from consortium.client.commands.home_interpreter_commands.list_client_connections import (
    ListClientConnectionsCommand,
)
from consortium.client.framework.base_interpreter import BaseInterpreter
from consortium.client.framework.base_parser import ParsedCommand
from consortium.client.objects.client_interpreter_objects import ClientInterpreterLexer
from consortium.client.utils.formatter_utils import export_rich_text_as_ansi
from consortium.client.utils.printer_utils import print_error, print_info


class DisconnectedInterpreter(BaseInterpreter):
    def __init__(self):
        disconnected_interpreter_core_commands = [
            *[
                command
                for command in CORE_COMMANDS
                if command.name not in ("home", "listeners", "generators", "agents")
            ],
            ConnectCommand(),
            ListClientConnectionsCommand(),
            InfoClientConnectionCommand(),
            DisconnectCommand(),
            RenameClientConnectionCommand(),
            InteractClientConnectionCommand(),
        ]
        super().__init__(
            prompt_session=PromptSession(
                message=ANSI(export_rich_text_as_ansi("[bold white]Consortium > ")),
                completer=NestedCompleter.from_nested_dict(
                    {
                        command.name: None
                        for command in disconnected_interpreter_core_commands
                    },
                ),
                auto_suggest=AutoSuggestFromHistory(),
            ),
            commands=[
                *disconnected_interpreter_core_commands,
            ],
            lexer=ClientInterpreterLexer(),
            ignore_keyboard_interrupt=True,
            environment={
                # Setting client_connection to None is mainly to signal to the banner
                # core command that there is no client connection to operate on.
                "client_connection": None,
                "commands": {
                    command.name: command
                    for command in disconnected_interpreter_core_commands
                },
            },
        )

    async def on_command_not_found(self, parsed_command: ParsedCommand) -> None:
        print_error(f"Command not found: {parsed_command.command}")

    async def on_interrupt(self) -> None:
        if self.ignore_keyboard_interrupt:
            print_error(
                "Keyboard interrupt ignored. Use 'exit' to exit the interpreter.",
            )
        else:
            print_info("Keyboard interrupt received. Exiting interpreter.")
