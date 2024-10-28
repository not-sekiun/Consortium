from typing import Any

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.commands.agents_interpreter_commands import (
    AGENTS_INTERPRETER_COMMANDS,
)
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.repl_interface.client_interpreter import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi
from consortium.client.utils.printer_utils import print_success

COMBINED_AGENTS_INTERPRETER_CORE_COMMANDS = [
    command for command in CORE_COMMANDS if command.name != "agents"
] + AGENTS_INTERPRETER_COMMANDS


class AgentsInterpreter(ClientInterpreter):
    def __init__(self, client_session: "ClientSession"):
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    "[bold white]Consortium ([bold red]Agents[bold white]) > ",
                ),
            ),
            commands=COMBINED_AGENTS_INTERPRETER_CORE_COMMANDS,
            client_session=client_session,
        )

    async def _update_autocomplete(self) -> None:
        all_agents = await self.environment[
            "client_rest_api_connection"
        ].get_all_agents()
        all_assets = await self.environment[
            "client_rest_api_connection"
        ].get_all_assets()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )

        # Register commands that take the agent ID as the first positional argument to
        # autocomplete with.
        agent_ids_completion = {agent["agent_id"]: None for agent in all_agents}
        for command in [
            "info_agent",
            "info_result",
            "info_task",
            "interact_agent",
            "list_results",
            "list_tasks",
            "rename_agent",
            "redescribe_agent",
        ]:
            nested_completer_dict[command] = agent_ids_completion

        # Register commands that take the asset ID as the first positional argument to
        # autocomplete with.
        assets_completion = {asset["resource_id"]: None for asset in all_assets}
        for command in ["download_asset", "info_asset"]:
            nested_completer_dict[command] = assets_completion

        # Register the help command to autocomplete with all available commands. This
        # includes all the newly added agent capability commands that are dynamically
        # added before this method is called.
        nested_completer_dict["help"] = {command: None for command in self.commands}

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    # We don't actually care about the event data so we just ignore it. We just need to
    # know a change happened so that we can update the autocompleter.
    async def _agent_registered_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        agent = await self.environment[
            "client_rest_api_connection"
        ].get_agent_by_agent_id(
            agent_id=event["data"]["agent_id"],
        )
        print_success(f"New agent '{agent["name"]}' ({agent["agent_id"]}) checked in.")
        await self._update_autocomplete()

    async def _setup_event_handlers(self) -> None:
        await self.environment["client_websockets_api_connection"].subscribe_to_event(
            event_type="AGENT_REGISTERED",
            event_handler=self._agent_registered_event_handler,
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
            event_type="AGENT_REGISTERED",
            event_handler=self._agent_registered_event_handler,
        )

    async def on_enter_interpreter(self) -> None:
        await self._update_autocomplete()
        await self._setup_event_handlers()

    async def on_exit_interpreter(self) -> None:
        # The exit command when executed will disconnect the websocket connection but
        # this method will still run so we need to first check if the client websockets
        # API connection has already been disconnected.
        if self.environment["client_websockets_api_connection"].connected:
            await self._teardown_event_handlers()
