from collections import deque
from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI, HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from rich.columns import Columns
from rich.panel import Panel
from rich.pretty import Pretty
from rich.text import Text

from consortium.client.exceptions.client_interpreter_exceptions import (
    UnclosedQuotesError,
)
from consortium.client.exceptions.rest_api_exceptions import (
    RestAPIOperationError,
)
from consortium.client.models.alias_model import Alias
from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.alias_expander import expand_aliases
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.repl_interface.lexer import tokenize
from consortium.client.repl_interface.parser import parse
from consortium.client.utils.printer_utils import console, print_error

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class BaseInterpreter:
    def __init__(
        self,
        prompt: str | ANSI | HTML | list[tuple[str, str]],
        commands: list[BaseCommand],
        aliases: dict[str, Alias],
        resource_commands: deque[str],
        client_session: ClientSession | None,
        interpreter_context: dict[str, Any] = None,
    ):
        if interpreter_context is None:
            interpreter_context = {}

        self.prompt_session = PromptSession(
            message=prompt,
            completer=NestedCompleter.from_nested_dict(
                {command.name: None for command in commands},
            ),
            auto_suggest=AutoSuggestFromHistory(),
            bottom_toolbar=self._get_bottom_toolbar_string,
        )
        self.commands = {command.name: command for command in commands}
        self.client_session = client_session
        self.interpreter_context = interpreter_context

        # Add current interpreter commands to the interpreter context for the `help`
        # command to access
        self.interpreter_context["commands"] = self.commands
        # Add aliases to the interpreter context for the `alias` command to access
        self.interpreter_context["aliases"] = aliases
        # Add the resource commands queue to the interpreter context for the `rc`
        # command to access
        self.interpreter_context["resource_commands"] = resource_commands

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

    async def on_loop(self) -> None: ...

    async def on_enter(self) -> None: ...

    async def on_exit(self) -> None: ...

    async def run(self) -> InterpreterSignal:
        await self.on_enter()

        while True:
            try:
                await self.on_loop()

                if self.interpreter_context["resource_commands"]:
                    input_string = self.interpreter_context[
                        "resource_commands"
                    ].popleft()
                    print_formatted_text(
                        HTML("<b><ansimagenta>[RC]</ansimagenta></b>"),
                        self.prompt_session.message,
                        end="",
                    )
                    print_formatted_text(input_string)
                else:
                    with patch_stdout(raw=True):
                        input_string = await self.prompt_session.prompt_async()
                if not input_string:
                    continue

                # Provide multi-line input functionality for unclosed quotes.
                try:
                    tokenized_string = tokenize(input_string=input_string)
                except UnclosedQuotesError:
                    previous_prompt = self.prompt_session.message
                    while True:
                        input_string += "\n" + await self.prompt_session.prompt_async(
                            message=". ",
                        )
                        try:
                            tokenized_string = tokenize(input_string=input_string)
                            # Calling prompt_async() with the message argument
                            # overwrites the previously set prompt message, so we
                            # reassign here to be able to call prompt_async() next time
                            # round with passing in a message argument.
                            self.prompt_session.message = previous_prompt
                            break
                        except UnclosedQuotesError:
                            continue

                expanded_tokens = expand_aliases(
                    tokens=tokenized_string.tokens,
                    aliases=self.interpreter_context["aliases"],
                )
                tokenized_string.tokens = expanded_tokens

                parsed_command = parse(tokenized_string=tokenized_string)
                if parsed_command.command in self.commands:
                    context = ConnectedContext(
                        command=parsed_command.command,
                        arguments=parsed_command.arguments,
                        raw_input=parsed_command.raw_input,
                        client_session=self.client_session,
                        interpreter_context=self.interpreter_context,
                    )
                    interpreter_signal = await self.commands[
                        parsed_command.command
                    ].run(context)

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
                else:
                    print_error(f"Command '{parsed_command.command}' not found")
            except KeyboardInterrupt:
                print_error(
                    "Keyboard interrupt ignored. Use 'exit' to exit the interpreter.",
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
                continue
            # except Exception as exc:
            #     print_error(
            #         f"Unhandled exception occurred. {exc.__class__.__name__}: {exc}"
            #     )
            #     console.print_exception(show_locals=True)
            #     continue

        raise AssertionError(
            "Interpreter REPL loop broke out without returning a valid interpreter "
            "signal."
        )
