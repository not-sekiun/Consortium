from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI, HTML, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.patch_stdout import patch_stdout

from consortium.client.exceptions.client_interpreter_exceptions import (
    UnclosedQuotesError,
)
from consortium.client.exceptions.rest_api_exceptions import (
    RestAPIOperationError,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)

# from consortium.client.repl_framework.base_interpreter import BaseInterpreter
from consortium.client.repl_interface.lexer import tokenize
from consortium.client.repl_interface.parser import parse
from consortium.client.utils.printer_utils import console, print_error

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class Interpreter:
    def __init__(
        self,
        prompt: str | ANSI | HTML | list[tuple[str, str]],
        commands: list[BaseCommand],
        client_session: ClientSession | None,
        context: dict[str, Any] = None,
    ):
        if context is None:
            context = {}

        # # TODO: Add resource commands and aliases to the environment variables at some
        # #  point
        # if context is None:
        #     context = {}

        # for key in context:
        #     if key in (
        #         "client_session",
        #         "rest_api",
        #         "websockets_api",
        #         "commands",
        #     ):
        #         raise AssertionError(
        #             f"Environment variable name '{key}' is reserved and cannot be used."
        #         )

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
        self.context = context

        # TODO: Deprecate
        self.environment = {
            "client_session": client_session,
            "rest_api": client_session.rest_api,
            "websockets_api": client_session.websockets_api,
            "commands": {command.name: command for command in commands},
            **context,
        }

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

    async def on_loop(self) -> None: ...

    async def on_enter(self) -> None: ...

    async def on_exit(self) -> None: ...

    async def run(self) -> ReturnStatus:
        await self.on_enter()

        while True:
            try:
                await self.on_loop()

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
                parsed_command = parse(tokenized_string=tokenized_string)
                if parsed_command.command in self.commands:
                    context = Context(
                        command=parsed_command.command,
                        arguments=parsed_command.arguments,
                        raw_input=parsed_command.raw_input,
                        client_session=self.client_session,
                        interpreter_context=self.context,
                        environment=self.environment,
                    )
                    command_return_status = await self.commands[
                        parsed_command.command
                    ].run(context)

                    if command_return_status.type == ReturnStatusType.CONTINUE:
                        continue
                    else:
                        await self.on_exit()
                        return command_return_status
                else:
                    print_error(f"Command '{parsed_command.command}' not found")
            except KeyboardInterrupt:
                print_error(
                    "Keyboard interrupt ignored. Use 'exit' to exit the interpreter.",
                )
            except Exception as exc:
                if isinstance(exc, RestAPIOperationError):
                    print_error(f"{exc}")
                    continue

                print_error(
                    f"Unhandled exception occurred. {exc.__class__.__name__}: {exc}"
                )
                console.print_exception(show_locals=True)
