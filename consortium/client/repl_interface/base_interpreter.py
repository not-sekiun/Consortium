from typing import Any

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
from consortium.client.client_websockets_events_api import EventHandler
from consortium.client.commands.resource_management_commands import (
    RESOURCE_MANAGEMENT_COMMANDS,
)
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
from consortium.client.repl_interface.autocompletes import (
    Autocomplete,
    AutocompleteResolutions,
    resolve_autocompletes,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.repl_interface.custom_completer import (
    CompletionsDict,
    CustomCompleter,
    custom_completer_filter_builder,
)
from consortium.client.repl_interface.lexer import tokenize
from consortium.client.repl_interface.parser import ParsedCommand, parse
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
        self.commands = {command.name: command for command in commands}
        # Built with no resolutions to start with: sentinels that need runtime data
        # complete to nothing until the interpreter rebuilds this in `on_enter`
        self.completer = CustomCompleter(
            completions_dict=self.build_completions_dict(),
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

    # Rebuilds the whole completions dictionary from what the commands themselves
    # declare, so autocompletion can never drift away from the commands it completes.
    def build_completions_dict(
        self,
        resolutions: AutocompleteResolutions | None = None,
    ) -> CompletionsDict:
        # The commands of the current interpreter are always resolvable so they are
        # provided here rather than by every interpreter individually
        resolutions = {Autocomplete.COMMANDS: list(self.commands)} | dict(
            resolutions or {},
        )
        # Keyed by the name the command is registered under rather than by
        # `command.name`, since dynamically registered commands (agent capabilities)
        # can be registered under a deconflicted name
        return {
            name: resolve_autocompletes(
                autocompletes=command.autocompletes,
                resolutions=resolutions,
            )
            for name, command in self.commands.items()
        }

    # The values this interpreter's commands declare their autocompletes against.
    # Overridden by interpreters that hold runtime data, calling `super()` first when
    # they extend another interpreter's resolutions.
    def get_autocomplete_resolutions(self) -> AutocompleteResolutions:
        return {}

    # Called by interpreters whenever the data behind their sentinels changes
    def refresh_autocomplete(self) -> None:
        self.completer.set_completions_dict(
            self.build_completions_dict(
                resolutions=self.get_autocomplete_resolutions(),
            ),
        )

    async def on_loop(self) -> None: ...

    async def on_enter(self) -> None: ...

    async def on_exit(self) -> None: ...

    # Wrappers around the `on_enter` and `on_exit` hooks the interpreters implement, so
    # that setup and teardown shared by a whole family of interpreters (see
    # `BaseConnectedInterpreter`) can be run around them without every interpreter
    # having to remember to call `super()`.
    async def _enter(self) -> None:
        await self.on_enter()

    async def _exit(self) -> None:
        await self.on_exit()

    async def run(self) -> InterpreterSignal:
        try:
            await self._enter()

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
                            await self._exit()
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
                "Unhandled exception occurred",
                exc=exc,
            )
            console.print_exception(show_locals=True)
            print_info("Exiting...")
            exit()

        raise AssertionError(
            "Interpreter REPL loop broke out without returning a valid interpreter "
            "signal."
        )


# Repository resources (assets, artifacts and payloads) belong to the server rather
# than to any one interpreter, so every connected interpreter registers the resource
# management commands and resolves the resource ID autocompletes they declare. Both are
# handled here rather than by the individual interpreters so that no interpreter can be
# left without them.
class BaseConnectedInterpreter(_BaseInterpreter[ClientSession]):
    def __init__(
        self,
        prompt: str | ANSI | HTML | list[tuple[str, str]],
        commands: list[BaseCommand],
        client_session: ClientSession,
        interpreter_context: BaseInterpreterContext,
    ):
        # Runtime IDs the resource autocomplete sentinels are resolved against. Held as
        # dictionaries so that the event handlers can add and remove single IDs while
        # preserving insertion order. Assigned before `super().__init__` since building
        # the completions dictionary resolves against them.
        self._asset_ids: dict[str, None] = {}
        self._artifact_ids: dict[str, None] = {}
        self._payload_ids: dict[str, None] = {}
        # Tracked so that teardown only ever unsubscribes handlers that were actually
        # subscribed (see `_enter`)
        self._resource_event_handlers_subscribed = False

        # An interpreter that registers a command of its own under one of these names
        # keeps its own command
        registered_command_names = {command.name for command in commands}
        super().__init__(
            prompt=prompt,
            commands=commands
            + [
                command
                for command in RESOURCE_MANAGEMENT_COMMANDS
                if command.name not in registered_command_names
            ],
            client_session=client_session,
            interpreter_context=interpreter_context,
        )

    def get_autocomplete_resolutions(self) -> AutocompleteResolutions:
        return super().get_autocomplete_resolutions() | {
            Autocomplete.ASSET_ID: self._asset_ids,
            Autocomplete.ARTIFACT_ID: self._artifact_ids,
            Autocomplete.PAYLOAD_ID: self._payload_ids,
        }

    async def _initialize_resource_autocompletes(self) -> None:
        all_assets = await self.client_session.rest_api.get_all_assets()
        all_artifacts = await self.client_session.rest_api.get_all_artifacts()
        all_payloads = await self.client_session.rest_api.get_all_payloads()

        self._asset_ids = dict.fromkeys(asset["resource_id"] for asset in all_assets)
        self._artifact_ids = dict.fromkeys(
            artifact["resource_id"] for artifact in all_artifacts
        )
        self._payload_ids = dict.fromkeys(
            payload["resource_id"] for payload in all_payloads
        )

        self.refresh_autocomplete()

    # Every resource event carries the resource's JSON as its data payload, so the
    # resource ID can be added to or removed from its completion set directly.
    async def _asset_created_event_handler(self, event: dict[str, Any]) -> None:
        self._asset_ids[event["data"]["resource_id"]] = None
        self.refresh_autocomplete()

    async def _asset_deleted_event_handler(self, event: dict[str, Any]) -> None:
        self._asset_ids.pop(event["data"]["resource_id"], None)
        self.refresh_autocomplete()

    async def _artifact_created_event_handler(self, event: dict[str, Any]) -> None:
        self._artifact_ids[event["data"]["resource_id"]] = None
        self.refresh_autocomplete()

    async def _artifact_deleted_event_handler(self, event: dict[str, Any]) -> None:
        self._artifact_ids.pop(event["data"]["resource_id"], None)
        self.refresh_autocomplete()

    async def _payload_created_event_handler(self, event: dict[str, Any]) -> None:
        self._payload_ids[event["data"]["resource_id"]] = None
        self.refresh_autocomplete()

    async def _payload_deleted_event_handler(self, event: dict[str, Any]) -> None:
        self._payload_ids.pop(event["data"]["resource_id"], None)
        self.refresh_autocomplete()

    # Single source of truth for the resource event subscriptions, so that setup and
    # teardown can never drift apart.
    def _get_resource_event_handlers(self) -> dict[str, EventHandler]:
        return {
            "ASSET_CREATED": self._asset_created_event_handler,
            "ASSET_DELETED": self._asset_deleted_event_handler,
            "ARTIFACT_CREATED": self._artifact_created_event_handler,
            "ARTIFACT_DELETED": self._artifact_deleted_event_handler,
            "PAYLOAD_CREATED": self._payload_created_event_handler,
            "PAYLOAD_DELETED": self._payload_deleted_event_handler,
        }

    async def _enter(self) -> None:
        # Run after the interpreter's own `on_enter` since it is that hook which starts
        # the websockets message handler loop. Subscribing to events that nothing is
        # consuming would leave those event messages sitting unread on the websocket
        # connection, so interpreters that never start the loop (the home interpreter)
        # get the one off resource ID fetch below and no live updates.
        await super()._enter()
        await self._initialize_resource_autocompletes()
        if self.client_session.websockets_api.running:
            await self.client_session.websockets_api.subscribe_to_events(
                event_handlers=self._get_resource_event_handlers(),
            )
            self._resource_event_handlers_subscribed = True

    async def _exit(self) -> None:
        # Unsubscribed before the interpreter's own `on_exit` runs, since that hook
        # stops the websockets message handler loop and disconnects the client session.
        if (
            self._resource_event_handlers_subscribed
            and self.client_session.websockets_api.connected
        ):
            await self.client_session.websockets_api.unsubscribe_from_events(
                event_handlers=self._get_resource_event_handlers(),
            )
            self._resource_event_handlers_subscribed = False
        await super()._exit()


class BaseDisconnectedInterpreter(_BaseInterpreter[None]): ...
