import traceback

from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter

import consortium.client.client_singletons as client_singletons
from consortium.client.client_exceptions import (
    RESTAPIError,
    UnclosedDoubleQuotesError,
    UnclosedSingleQuotesError,
)
from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.commands.disconnected_interpreter_commands.disconnect import (
    DisconnectCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.info_client_connection import (
    InfoClientConnectionCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.redescribe_client_connection import (
    RedescribeClientConnectionCommand,
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
from consortium.client.objects.client_return_status_objects import ReturnStatusType
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi
from consortium.client.utils.printer_utils import CONSOLE, print_error, print_info

client_connections_service = client_singletons.client_connections_service


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
            RedescribeClientConnectionCommand(),
        ]
        super().__init__(
            prompt_session=PromptSession(
                message=ANSI(format_rich_text_as_ansi("[bold white]Consortium > ")),
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

    # TODO: Provide more comprehensive error handling in the commands.
    # In general, when an error is raised on the REST API side we simply print the error
    # message to the console and interrupt whichever operation we were attempting to do.
    async def on_interpreter_errored(self, exc: Exception) -> None:
        if isinstance(exc, RESTAPIError):
            print_error(f"Error: {exc}")
        else:
            print_error(f"Fatal error occurred: {exc}")
            CONSOLE.print(f"[bold red]{traceback.format_exc()}")

    # TODO: Find a way for interpreters to "inherit" command completions or share
    #  common command completions. Probably could just make it a parameter
    async def on_interpreter_loop(self) -> None:
        all_client_connections = client_connections_service.get_all_client_connections()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            nested_completer=self.prompt_session.completer,
        )
        for key, value in {
            command: {
                str(client_connection.client_connection_id): None
                for client_connection in all_client_connections
            }
            for command in [
                "disconnect",
                "info_client_connection",
                "interact_client_connection",
                "rename_client_connection",
                "redescribe_client_connection",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = {command: None for command in self.commands}

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    # TODO: Find a better way to add multiline support without needing to rewrite the
    #  entire interpreter run loop part.
    async def run_interpreter(self):
        await self.on_enter_interpreter()

        while True:
            try:
                await self.on_interpreter_loop()

                input_string = await self.read_input()

                if not input_string:
                    continue

                # Provide multi-line input functionality for unclosed quotes.
                try:
                    tokens = self.lexer.tokenize(input_string)
                except (UnclosedDoubleQuotesError, UnclosedSingleQuotesError):
                    previous_prompt = self.prompt_session.message
                    while True:
                        input_string += "\n" + await self.prompt_session.prompt_async(
                            message="... ",
                        )
                        try:
                            tokens = self.lexer.tokenize(input_string)
                            # Calling prompt_async() with the message argument
                            # overwrites the previously set prompt message, so we
                            # reassign here to be able to call prompt_async() next time
                            # round with passing in a message argument.
                            self.prompt_session.message = previous_prompt
                            break
                        except (UnclosedDoubleQuotesError, UnclosedSingleQuotesError):
                            continue

                parsed_command = self.parser.parse(tokens)

                if parsed_command.command in self.commands:
                    command_return_status = await self.on_command(parsed_command)
                    if command_return_status.type == ReturnStatusType.CONTINUE:
                        continue
                    else:
                        return command_return_status
                else:
                    await self.on_command_not_found(parsed_command)
            except KeyboardInterrupt:
                await self.on_interrupt()
                if not self.ignore_keyboard_interrupt:
                    break
            except Exception as exc:
                await self.on_interpreter_errored(exc)

        await self.on_exit_interpreter()
