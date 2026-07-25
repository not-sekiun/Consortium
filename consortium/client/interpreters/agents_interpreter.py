from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI
from prompt_toolkit.completion import PathCompleter

from consortium.client.commands.agents_interpreter_commands import (
    AGENTS_INTERPRETER_COMMANDS,
    AgentListCommand,
)
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.repl_interface.base_interpreter import (
    BaseConnectedInterpreter,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi
from consortium.client.utils.printer_utils import print_success

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


COMBINED_AGENTS_INTERPRETER_CORE_COMMANDS = [
    command for command in CORE_COMMANDS if command.name != "agents"
] + AGENTS_INTERPRETER_COMMANDS

# Commands that take an asset resource ID as their first positional argument, and so
# autocomplete against the set of known asset IDs. Kept as a single source of truth so
# the initial autocompleter population and the asset event handlers stay in sync.
ASSET_ID_COMPLETION_COMMANDS = ["as-dl", "as-info", "as-rm"]

# Commands that take an artifact resource ID as their first positional argument, and so
# autocomplete against the set of known artifact IDs.
ARTIFACT_ID_COMPLETION_COMMANDS = ["ar-dl", "ar-info", "ar-rm"]


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
        all_artifacts = await self.client_session.rest_api.get_all_artifacts()

        completions_dict = self.completer.get_completions_dict()

        # Register commands that take the agent ID as the first positional argument to
        # autocomplete with.
        agent_ids_completion = {agent["agent_id"]: None for agent in all_agents}
        for command in ["info", "interact", "t-list", "rename", "describe", "delete"]:
            completions_dict[command] = agent_ids_completion

        # Register commands that take the task ID as the first positional
        # argument to autocomplete with.
        all_tasks = await self.client_session.rest_api.get_all_agent_tasks()
        task_ids_completion = {task["task_id"]: None for task in all_tasks}
        for command in ["t-info", "watch"]:
            completions_dict[command] = task_ids_completion

        # Register commands that take the asset resource ID as the first positional
        # argument to autocomplete with.
        assets_completion = {asset["resource_id"]: None for asset in all_assets}
        for command in ASSET_ID_COMPLETION_COMMANDS:
            completions_dict[command] = assets_completion

        # Register commands that take the artifact resource ID as the first positional
        # argument to autocomplete with.
        artifacts_completion = {
            artifact["resource_id"]: None for artifact in all_artifacts
        }
        for command in ARTIFACT_ID_COMPLETION_COMMANDS:
            completions_dict[command] = artifacts_completion

        # Register the help command to autocomplete with all available commands. This
        # includes all the newly added agent capability commands that are dynamically
        # added before this method is called.
        completions_dict["help"] = dict.fromkeys(self.commands)

        # Register the asset upload command to autocomplete with all available files.
        completions_dict["up"] = PathCompleter()

        self.completer.set_completions_dict(completions_dict)

    async def _agent_tasked_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        task = event["data"]["task"]
        completions_dict = self.completer.get_completions_dict()
        completions_dict["t-info"][task["task_id"]] = None
        self.completer.set_completions_dict(completions_dict)

    async def _agent_registered_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        agent = event["data"]
        print_success(f"New agent '{agent['name']}' ({agent['agent_id']}) checked in")

        completions_dict = self.completer.get_completions_dict()
        for command in ["info", "interact", "t-list", "rename", "describe", "delete"]:
            completions_dict[command][agent["agent_id"]] = None
        self.completer.set_completions_dict(completions_dict)

    async def _agent_deleted_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        # The AGENT_DELETED event carries the deleted agent's JSON alongside a snapshot
        # of the task IDs it owned at deletion time. The agent's tasks are removed along
        # with the agent server side, so both the agent ID and every one of its task IDs
        # must be pruned from their respective completion sets.
        agent = event["data"]["agent"]
        task_ids = event["data"]["task_ids"]
        completions_dict = self.completer.get_completions_dict()
        for command in ["info", "interact", "t-list", "rename", "describe", "delete"]:
            completions_dict[command].pop(agent["agent_id"], None)
        for command in ["t-info", "watch"]:
            for task_id in task_ids:
                completions_dict[command].pop(task_id, None)
        self.completer.set_completions_dict(completions_dict)

    async def _asset_created_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        # The ASSET_CREATED event carries the created asset's JSON as its data payload,
        # so its resource ID can be added to every asset ID completion set directly.
        asset = event["data"]
        completions_dict = self.completer.get_completions_dict()
        for command in ASSET_ID_COMPLETION_COMMANDS:
            completions_dict[command][asset["resource_id"]] = None
        self.completer.set_completions_dict(completions_dict)

    async def _asset_deleted_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        asset = event["data"]
        completions_dict = self.completer.get_completions_dict()
        for command in ASSET_ID_COMPLETION_COMMANDS:
            completions_dict[command].pop(asset["resource_id"], None)
        self.completer.set_completions_dict(completions_dict)

    async def _artifact_created_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        artifact = event["data"]
        completions_dict = self.completer.get_completions_dict()
        for command in ARTIFACT_ID_COMPLETION_COMMANDS:
            completions_dict[command][artifact["resource_id"]] = None
        self.completer.set_completions_dict(completions_dict)

    async def _artifact_deleted_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        artifact = event["data"]
        completions_dict = self.completer.get_completions_dict()
        for command in ARTIFACT_ID_COMPLETION_COMMANDS:
            completions_dict[command].pop(artifact["resource_id"], None)
        self.completer.set_completions_dict(completions_dict)

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
            event_type="AGENT_DELETED",
            event_handler=self._agent_deleted_event_handler,
        )
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="ASSET_CREATED",
            event_handler=self._asset_created_event_handler,
        )
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="ASSET_DELETED",
            event_handler=self._asset_deleted_event_handler,
        )
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="ARTIFACT_CREATED",
            event_handler=self._artifact_created_event_handler,
        )
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="ARTIFACT_DELETED",
            event_handler=self._artifact_deleted_event_handler,
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
            event_type="AGENT_DELETED",
            event_handler=self._agent_deleted_event_handler,
        )
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="ASSET_CREATED",
            event_handler=self._asset_created_event_handler,
        )
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="ASSET_DELETED",
            event_handler=self._asset_deleted_event_handler,
        )
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="ARTIFACT_CREATED",
            event_handler=self._artifact_created_event_handler,
        )
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="ARTIFACT_DELETED",
            event_handler=self._artifact_deleted_event_handler,
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
