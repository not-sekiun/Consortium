from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter, PathCompleter

from consortium.client.commands.agents_interpreter_commands import (
    AGENTS_INTERPRETER_COMMANDS,
    AgentListCommand,
)
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.repl_interface.base_interpreter import (
    BaseConnectedInterpreter,
)
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi
from consortium.client.utils.printer_utils import print_success

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


COMBINED_AGENTS_INTERPRETER_CORE_COMMANDS = [
    command for command in CORE_COMMANDS if command.name != "agents"
] + AGENTS_INTERPRETER_COMMANDS


class AgentsInterpreter(BaseConnectedInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        interpreter_context: BaseInterpreterContext,
    ):
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    "[bold white]Consortium ([bold red]Agents[bold white])\n> ",
                ),
            ),
            commands=COMBINED_AGENTS_INTERPRETER_CORE_COMMANDS,
            client_session=client_session,
            interpreter_context=interpreter_context,
        )

    async def _initialize_autocompleter(
        self,
        all_agents: list[dict[str, Any]],
    ) -> None:
        all_assets = await self.client_session.rest_api.get_all_assets()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )

        # Register commands that take the agent ID as the first positional argument to
        # autocomplete with.
        agent_ids_completion = {agent["agent_id"]: None for agent in all_agents}
        for command in [
            "info",
            "interact",
            # "r-list",
            "t-list",
            "rename",
            "describe",
        ]:
            nested_completer_dict[command] = agent_ids_completion

        # Register commands that take the task or result ID as the first positional
        # argument to autocomplete with.
        all_tasks = await self.client_session.rest_api.get_all_agent_tasks()
        for command in ["t-info", "watch"]:
            nested_completer_dict[command] = {
                task["task_id"]: None for task in all_tasks
            }
        # all_results = await self.client_session.rest_api.get_all_agent_results()
        # nested_completer_dict["r-info"] = {
        #     result["result_id"]: None for result in all_results
        # }

        # Register commands that take the asset ID as the first positional argument to
        # autocomplete with.
        assets_completion = {asset["resource_id"]: None for asset in all_assets}
        for command in ["as-dl", "as-info"]:
            nested_completer_dict[command] = assets_completion

        # Register the help command to autocomplete with all available commands. This
        # includes all the newly added agent capability commands that are dynamically
        # added before this method is called.
        nested_completer_dict["help"] = dict.fromkeys(self.commands)

        # Register the asset upload command to autocomplete with all available files.
        nested_completer_dict["up"] = PathCompleter()

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    async def _agent_tasked_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        task = event["data"]["task"]

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        nested_completer_dict["t-info"][task["task_id"]] = None
        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    async def _agent_result_received_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        result = event["data"]["result"]

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        nested_completer_dict["r-info"][result["result_id"]] = None
        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    async def _agent_registered_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        agent = event["data"]
        print_success(f"New agent '{agent['name']}' ({agent['agent_id']}) checked in")

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        for command in [
            "info",
            "interact",
            # "r-list",
            "t-list",
            "rename",
            "describe",
        ]:
            nested_completer_dict[command][agent["agent_id"]] = None
        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    async def _setup_event_handlers(self) -> None:
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="AGENT_REGISTERED",
            event_handler=self._agent_registered_event_handler,
        )
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="AGENT_TASKED",
            event_handler=self._agent_tasked_event_handler,
        )
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="AGENT_RESULT_RECEIVED",
            event_handler=self._agent_result_received_event_handler,
        )
        await self.client_session.websockets_api.start()

    async def _teardown_event_handlers(self) -> None:
        # Stop the message consumption loop for the websocket connection just so that
        # the action message being sent next doesn't need to go through the message
        # consumer handler loop. This is not necessary but just makes it cleaner.
        await self.client_session.websockets_api.stop()
        # Remove all relevant event handlers to prevent them from firing in other
        # interpreters.
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="AGENT_REGISTERED",
            event_handler=self._agent_registered_event_handler,
        )
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="AGENT_TASKED",
            event_handler=self._agent_tasked_event_handler,
        )
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="AGENT_RESULT_RECEIVED",
            event_handler=self._agent_result_received_event_handler,
        )

    async def on_enter(self) -> None:
        all_agents = await self.client_session.rest_api.get_all_agents()
        await self._initialize_autocompleter(all_agents=all_agents)
        await self._setup_event_handlers()
        AgentListCommand._list_all_agents(all_agents=all_agents)

    async def on_exit(self) -> None:
        # The exit command when executed will disconnect the websocket connection but
        # this method will still run so we need to first check if the client websockets
        # API connection has already been disconnected.
        if self.client_session.websockets_api.connected:
            await self._teardown_event_handlers()
