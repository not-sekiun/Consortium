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
            # lexer=Lexer(),
            # ignore_keyboard_interrupt=True,
            # environment={
            #     # Setting `client_session`, `rest_api`, and
            #     # `websockets_api` to `None` is mainly to signal to
            #     # the banner core command that there is no client session to operate
            #     # on.
            #     "client_session": None,
            #     "rest_api": None,
            #     "websockets_api": None,
            #     "commands": {
            #         command.name: command
            #         for command in combined_disconnected_interpreter_core_commands
            #     },
            # },
        )

    # async def on_command_not_found(self, parsed_command: ParsedCommand) -> None:
    #     print_error(f"Command not found: {parsed_command.command}")

    # async def on_interrupt(self) -> None:
    #     if self.ignore_keyboard_interrupt:
    #         print_error(
    #             "Keyboard interrupt ignored. Use 'exit' to exit the interpreter.",
    #         )
    #     else:
    #         print_info("Keyboard interrupt received. Exiting interpreter.")

    # # TODO: Provide more comprehensive error handling in the commands.
    # # In general, when an error is raised on the REST API side we simply print the error
    # # message to the console and interrupt whichever operation we were attempting to do.
    # async def on_error(self, exc: Exception) -> None:
    #     if isinstance(exc, RestAPIOperationError):
    #         print_error(f"Error: {exc}")
    #     else:
    #         print_error(f"Fatal error occurred: {exc}")
    #         console.print(f"[bold red]{traceback.format_exc()}")

    # TODO: Find a way for interpreters to "inherit" command completions or share
    #  common command completions. Probably could just make it a parameter
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

    # # TODO: Find a better way to add multiline support without needing to rewrite the
    # #  entire interpreter run loop part.
    # async def run(self):
    #     await self.on_enter()
    #
    #     while True:
    #         try:
    #             await self.on_loop()
    #
    #             input_string = await self.read_input()
    #
    #             if not input_string:
    #                 continue
    #
    #             # Provide multi-line input functionality for unclosed quotes.
    #             try:
    #                 tokens = self.lexer.tokenize(input_string)
    #             except UnclosedQuotesError:
    #                 previous_prompt = self.prompt_session.message
    #                 while True:
    #                     input_string += "\n" + await self.prompt_session.prompt_async(
    #                         message="... ",
    #                     )
    #                     try:
    #                         tokens = self.lexer.tokenize(input_string)
    #                         # Calling prompt_async() with the message argument
    #                         # overwrites the previously set prompt message, so we
    #                         # reassign here to be able to call prompt_async() next time
    #                         # round with passing in a message argument.
    #                         self.prompt_session.message = previous_prompt
    #                         break
    #                     except UnclosedQuotesError:
    #                         continue
    #
    #             parsed_command = self.parser.parse(tokens)
    #
    #             if parsed_command.command in self.commands:
    #                 command_return_status = await self.on_command(parsed_command)
    #                 if command_return_status.type == ReturnStatusType.CONTINUE:
    #                     continue
    #                 else:
    #                     return command_return_status
    #             else:
    #                 await self.on_command_not_found(parsed_command)
    #         except KeyboardInterrupt:
    #             await self.on_interrupt()
    #             if not self.ignore_keyboard_interrupt:
    #                 break
    #         except Exception as exc:
    #             await self.on_error(exc)
    #
    #     await self.on_exit()
