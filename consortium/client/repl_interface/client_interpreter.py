import traceback

from prompt_toolkit import ANSI, HTML, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.patch_stdout import patch_stdout

from consortium.client.exceptions.client_interpreter_exceptions import (
    UnclosedDoubleQuotesError,
    UnclosedSingleQuotesError,
)
from consortium.client.exceptions.client_rest_api_connection_exceptions import (
    ClientRESTAPIOperationError,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import BaseCommand, ReturnStatus
from consortium.client.repl_framework.base_interpreter import BaseInterpreter
from consortium.client.repl_framework.base_parser import ParsedCommand
from consortium.client.repl_interface.client_interpreter_lexer import (
    ClientInterpreterLexer,
)
from consortium.client.utils.printer_utils import CONSOLE, print_error, print_info


class ClientInterpreter(BaseInterpreter):
    def __init__(
        self,
        prompt: str | ANSI | HTML | list[tuple[str, str]],
        commands: list[BaseCommand],
        client_session: "ClientSession",
        additional_environment_variables: dict[str, any] = None,
    ):
        # TODO: Add resource commands and aliases to the environment variables at some
        #  point
        if additional_environment_variables is None:
            additional_environment_variables = {}

        for key in additional_environment_variables:
            assert key not in (
                "client_session",
                "client_rest_api_connection",
                "client_websockets_api_connection",
                "commands",
            ), f"Environment variable name '{key}' is reserved and cannot be used."

        super().__init__(
            prompt_session=PromptSession(
                message=prompt,
                completer=NestedCompleter.from_nested_dict(
                    {command.name: None for command in commands},
                ),
                auto_suggest=AutoSuggestFromHistory(),
                bottom_toolbar=self._get_bottom_toolbar_string,
            ),
            commands=commands,
            ignore_keyboard_interrupt=True,
            environment={
                "client_session": client_session,
                "client_rest_api_connection": client_session.client_rest_api_connection,
                "client_websockets_api_connection": client_session.client_websockets_api_connection,
                "commands": {command.name: command for command in commands},
                **additional_environment_variables,
            },
            lexer=ClientInterpreterLexer(),
        )

    # We provide a function because it needs to be called on every prompt update. The
    # name of the session can be renamed at any moment. Just passing in `HTML` object
    # to the `bottom_toolbar` parameter does not cause that `HTML` object to be updated
    # on every prompt.
    def _get_bottom_toolbar_string(self) -> HTML:
        client_session = self.environment["client_session"]
        return HTML(
            f"<bold>Current client session: {client_session} | Server: "
            f"{client_session.remote_host}:{client_session.remote_port} | "
            f"Logged in as: {client_session.username}</bold>",
        )

    async def read_input(
        self,
    ) -> str:
        with patch_stdout(raw=True):
            return await super().read_input()

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
        if isinstance(exc, ClientRESTAPIOperationError):
            print_error(f"Error: {exc}")
        else:
            print_error(f"Fatal error occurred: {exc}")
            CONSOLE.print(f"[bold red]{traceback.format_exc()}")

    async def run_interpreter(self) -> ReturnStatus:
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
                    if command_return_status.type == ClientReturnStatusType.CONTINUE:
                        continue
                    else:
                        await self.on_exit_interpreter()
                        return command_return_status
                else:
                    await self.on_command_not_found(parsed_command)
            except KeyboardInterrupt:
                await self.on_interrupt()
                if not self.ignore_keyboard_interrupt:
                    await self.on_exit_interpreter()
                    return ReturnStatus(type=ClientReturnStatusType.EXIT)
            except Exception as exc:
                await self.on_interpreter_errored(exc)
