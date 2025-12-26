from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI, HTML
from prompt_toolkit.completion import NestedCompleter

from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.listeners_interpreter_commands import (
    LISTENERS_INTERPRETER_COMMANDS,
)
from consortium.client.repl_framework.base_command import BaseCommand
from consortium.client.repl_interface.client_interpreter import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


COMBINED_LISTENERS_INTERPRETER_CORE_COMMANDS = [
    command for command in CORE_COMMANDS if command.name != "listeners"
] + LISTENERS_INTERPRETER_COMMANDS


class ListenersInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        prompt: str | ANSI | HTML | list[tuple[str, str]] | None = None,
        commands: list[BaseCommand] | None = None,
        additional_environment_variables: dict[str, Any] | None = None,
    ):
        if prompt is None:
            prompt = HTML(
                "<b>Consortium (<ansiblue>Listeners</ansiblue>) > </b>",
            )
        if commands is None:
            commands = COMBINED_LISTENERS_INTERPRETER_CORE_COMMANDS
        if additional_environment_variables is None:
            additional_environment_variables = {}

        super().__init__(
            prompt=prompt,
            commands=commands,
            client_session=client_session,
            additional_environment_variables=additional_environment_variables,
        )

    async def _update_autocomplete(self) -> None:
        all_listeners = await self.environment[
            "client_rest_api_connection"
        ].get_all_listeners()
        all_listener_templates = await self.environment[
            "client_rest_api_connection"
        ].get_all_listener_templates()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        for key, value in {
            command: {listener["listener_id"]: None for listener in all_listeners}
            for command in [
                "start",
                "stop_listener",
                "cancel_listener",
                "delete_listener",
                "info_listener",
                "rename_listener",
                "redescribe_listener",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {
                listener_template["listener_template_id"]: None
                for listener_template in all_listener_templates
            }
            for command in [
                "info_listener_template",
                "use_listener_template",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {
                listener["listener_id"]: dict.fromkeys(listener["parameters"])
                for listener in all_listeners
            }
            for command in [
                "set_listener_parameter",
                "unset_listener_parameter",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = dict.fromkeys(self.commands)

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    # We don't actually care about the event data so we just ignore it. We just need to
    # know a change happened so that we can update the autocompleter.
    async def _listener_created_or_removed_event_handler(
        self,
        _event: dict[str, Any],
    ) -> None:
        await self._update_autocomplete()

    async def _setup_event_handlers(self) -> None:
        await self.environment["client_websockets_api_connection"].subscribe_to_event(
            event_type="LISTENER_CREATED",
            event_handler=self._listener_created_or_removed_event_handler,
        )
        await self.environment["client_websockets_api_connection"].subscribe_to_event(
            event_type="LISTENER_REMOVED",
            event_handler=self._listener_created_or_removed_event_handler,
        )
        await self.environment["client_websockets_api_connection"].start()

    async def _teardown_event_handlers(self) -> None:
        # Stop the message consumption loop for the websocket connection just so that
        # the action message being sent next doesn't need to go through the message
        # consumer handler loop. This is not necessary but just makes it cleaner.
        await self.environment["client_websockets_api_connection"].stop()
        # Remove all relevant event handlers to prevent them from firing in other
        # interpreters.
        await self.environment[
            "client_websockets_api_connection"
        ].unsubscribe_from_event(
            event_type="LISTENER_CREATED",
            event_handler=self._listener_created_or_removed_event_handler,
        )
        await self.environment[
            "client_websockets_api_connection"
        ].unsubscribe_from_event(
            event_type="LISTENER_REMOVED",
            event_handler=self._listener_created_or_removed_event_handler,
        )

    async def on_enter(self) -> None:
        await self._update_autocomplete()
        await self._setup_event_handlers()

    async def on_exit(self) -> None:
        # The exit command when executed will disconnect the websocket connection but
        # this method will still run so we need to first check if the client websockets
        # API connection has already been disconnected.
        if self.environment["client_websockets_api_connection"].connected:
            await self._teardown_event_handlers()
