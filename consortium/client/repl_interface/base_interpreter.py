from aiohttp import ClientConnectionError
from prompt_toolkit import ANSI, HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.patch_stdout import patch_stdout
from rich.columns import Columns
from rich.panel import Panel
from rich.pretty import Pretty
from rich.text import Text
from websockets.exceptions import ConnectionClosed

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.exceptions.client_interpreter_exceptions import (
    UnclosedQuotesError,
)
from consortium.client.exceptions.rest_api_exceptions import (
    RestAPIOperationError,
)
from consortium.client.models.command_info_model import CommandInfo
from consortium.client.models.context_models import (
    ConnectedContext,
    DisconnectedContext,
)
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    ExitClientSessionSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.alias_expander import expand_aliases
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.repl_interface.custom_completer import (
    CustomCompleter,
    custom_completer_filter_builder,
)
from consortium.client.repl_interface.lexer import tokenize
from consortium.client.repl_interface.parser import ParsedCommand, parse
from consortium.client.utils.formatter_utils import format_exc_as_message
from consortium.client.utils.printer_utils import console, print_error, print_info

_client_sessions_service = client_singletons.client_sessions_service


class _BaseInterpreter[TClientSession: (ClientSession, None)]:
    def __init__(
        self,
        prompt: str | ANSI | HTML | list[tuple[str, str]],
        commands: list[BaseCommand],
        client_session: TClientSession,
        interpreter_context: BaseInterpreterContext,
    ):
        self.completer = CustomCompleter(
            completions_dict={command.name: None for command in commands}
        )
        self.prompt_session = PromptSession(
            message=prompt,
            completer=self.completer,
            auto_suggest=AutoSuggestFromHistory(),
            bottom_toolbar=self._get_bottom_toolbar_string,
            complete_while_typing=custom_completer_filter_builder(
                custom_completer=self.completer
            ),
        )
        self.commands = {command.name: command for command in commands}
        self.client_session = client_session
        self.interpreter_context = interpreter_context

        # Add current interpreter commands to the interpreter context for the `help`
        # command to access.
        self.interpreter_context.commands_info = {
            command.name: CommandInfo(
                name=command.name,
                description=command.description,
                group=command.group,
                summary=command.summary,
            )
            for command in commands
        }

    # We provide a function because it needs to be called on every prompt update. The
    # name of the session can be renamed at any moment. Just passing in `HTML` object
    # to the `bottom_toolbar` parameter does not cause that `HTML` object to be updated
    # on every prompt.
    def _get_bottom_toolbar_string(self) -> HTML:
        if not self.client_session:
            return HTML(
                "<b><ansired> DISCONNECTED </ansired></b><b> Use the 'connect' "
                "command to connect to a server</b>"
            )
        return HTML(
            f"<b><ansigreen> CONNECTED </ansigreen></b><b> Current client session: "
            f"{self.client_session} | Server: "
            f"{self.client_session.remote_host}:{self.client_session.remote_port} | "
            f"Logged in as: {self.client_session.username}</b>",
        )

    async def _get_raw_input(self, multiline_input: bool = False) -> str:
        # Check for any queued up resource commands and return those if they exist
        if self.interpreter_context.resource_commands:
            input_string = self.interpreter_context.resource_commands.popleft()
            print_formatted_text(
                HTML("<b><ansimagenta>[RC]</ansimagenta></b>"),
                ". " if multiline_input else self.prompt_session.message,
                end="",
            )
            print_formatted_text(input_string)
            return input_string

        with patch_stdout(raw=True):
            return await self.prompt_session.prompt_async(
                message=". " if multiline_input else None
            )

    async def _get_complete_input(self) -> str:
        # Get the first valid input possible from either resource commands or stdin
        input_string = await self._get_raw_input()

        # Provide multi-line input functionality for unclosed quotes, attempt to test
        # for incomplete quotes by tokenizing first, if tokenization detects unclosed
        # quotes we fall through to the multiline portion
        try:
            tokenize(input_string=input_string)
            return input_string
        except UnclosedQuotesError:
            pass

        # Read in multiline input
        previous_prompt = self.prompt_session.message
        try:
            while True:
                input_string += "\n" + await self._get_raw_input(multiline_input=True)
                try:
                    tokenize(input_string=input_string)
                    break
                except UnclosedQuotesError:
                    continue
        finally:
            # Calling `prompt_async()` with the message argument overwrites the
            # previously set prompt message, so we reassign here to be able to call
            # `prompt_async()` next time round passing in a message argument. We set
            # it in the finally block to guarantee reassignment even if an exception
            # bubbles up (eg a `KeyboardInterrupt`)
            self.prompt_session.message = previous_prompt

        return input_string

    def _parse_input_string(self, input_string: str) -> ParsedCommand:
        tokenized_string = tokenize(input_string=input_string)
        expanded_tokens = expand_aliases(
            tokens=tokenized_string.tokens,
            aliases=self.interpreter_context.aliases,
        )
        tokenized_string.tokens = expanded_tokens
        return parse(tokenized_string=tokenized_string)

    async def _dispatch_command(
        self, parsed_command: ParsedCommand
    ) -> InterpreterSignal:
        if parsed_command.command not in self.commands:
            print_error(f"Command '{parsed_command.command}' not found")
            return ContinueSignal()

        return await self.commands[parsed_command.command].run(
            context=ConnectedContext(
                command=parsed_command.command,
                arguments=parsed_command.arguments,
                raw_input=parsed_command.raw_input,
                client_session=self.client_session,
                interpreter_context=self.interpreter_context,
            )
            if self.client_session is not None
            else DisconnectedContext(
                command=parsed_command.command,
                arguments=parsed_command.arguments,
                raw_input=parsed_command.raw_input,
                interpreter_context=self.interpreter_context,
            )
        )

    async def on_loop(self) -> None: ...

    async def on_enter(self) -> None: ...

    async def on_exit(self) -> None: ...

    async def run(self) -> InterpreterSignal:
        try:
            await self.on_enter()

            while True:
                try:
                    await self.on_loop()

                    input_string = await self._get_complete_input()
                    if not input_string:
                        continue
                    parsed_command = self._parse_input_string(input_string=input_string)
                    interpreter_signal = await self._dispatch_command(
                        parsed_command=parsed_command,
                    )
                    match interpreter_signal:
                        case ContinueSignal():
                            continue
                        case InterpreterSignal():
                            await self.on_exit()
                            return interpreter_signal
                        case _:
                            raise AssertionError(
                                "Unsupported interpreter signal returned from command. "
                                f"Received signal '{interpreter_signal}'",
                            )
                except KeyboardInterrupt:
                    print_error(
                        "Keyboard interrupt ignored. Use 'exit' to exit the "
                        "interpreter.",
                    )
                except RestAPIOperationError as exc:
                    print_error(f"{exc}")
                    if exc.detail:
                        console.print(
                            Columns(
                                [
                                    Text("╰─", style="bold cyan"),
                                    Panel(
                                        Pretty(exc.detail),
                                        title="Error Detail",
                                        style="bold cyan",
                                        expand=False,
                                        title_align="left",
                                    ),
                                ],
                                expand=False,
                                padding=(0, 0),
                            )
                        )

                    # Check for case where our access was revoked mid-session or the
                    # server restarted causing the JWT to be invalidated
                    if exc.status_code == 401:
                        print_info(
                            "Current session access was remotely revoked. Removing current "
                            "session and returning to disconnected interpreter..."
                        )
                        await _client_sessions_service.remove_client_session_by_client_session_id(
                            client_session_id=self.client_session.client_session_id
                        )
                        return ExitClientSessionSignal()
        except RestAPIOperationError as exc:
            # Check for case where our access was revoked mid-session or the
            # server restarted causing the JWT to be invalidated
            if exc.status_code == 401:
                print_info(
                    "Current session access was remotely revoked. Removing current "
                    "session and returning to disconnected interpreter..."
                )
                await (
                    _client_sessions_service.remove_client_session_by_client_session_id(
                        client_session_id=self.client_session.client_session_id
                    )
                )
                return ExitClientSessionSignal()
        # Check for case where connection to the remote server was lost mid-session
        except ClientConnectionError, ConnectionClosed:
            print_error(
                "Connection to server lost. Removing current session and returning "
                "to disconnected interpreter..."
            )
            await _client_sessions_service.remove_client_session_by_client_session_id(
                client_session_id=self.client_session.client_session_id
            )
            return ExitClientSessionSignal()
        except Exception as exc:
            print_error(
                f"Unhandled exception occurred. {format_exc_as_message(exc=exc)}"
            )
            console.print_exception(show_locals=True)
            print_info("Exiting...")
            exit()

        raise AssertionError(
            "Interpreter REPL loop broke out without returning a valid interpreter "
            "signal."
        )


class BaseConnectedInterpreter(_BaseInterpreter[ClientSession]): ...


class BaseDisconnectedInterpreter(_BaseInterpreter[None]): ...
