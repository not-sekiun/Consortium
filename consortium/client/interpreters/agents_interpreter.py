from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI

from consortium.client.client_websockets_events_api import EventHandler
from consortium.client.commands.agents_interpreter_commands import (
    AGENTS_INTERPRETER_COMMANDS,
    AgentListCommand,
)
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.repl_interface.autocompletes import (
    Autocomplete,
    AutocompleteResolutions,
)
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


class AgentsInterpreter(BaseConnectedInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        interpreter_context: BaseInterpreterContext,
    ):
        # Runtime IDs the autocomplete sentinels of this interpreter's commands are
        # resolved against. Held as dictionaries so that the event handlers can add and
        # remove single IDs while preserving insertion order.
        self._agent_ids: dict[str, None] = {}
        self._task_ids: dict[str, None] = {}

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

    def get_autocomplete_resolutions(self) -> AutocompleteResolutions:
        return super().get_autocomplete_resolutions() | {
            Autocomplete.AGENT_ID: self._agent_ids,
            Autocomplete.AGENT_TASK_ID: self._task_ids,
        }

    async def _initialize_autocompleter(
        self,
        all_agents: list[dict[str, Any]],
    ) -> None:
        all_tasks = await self.client_session.rest_api.get_all_agent_tasks()

        self._agent_ids = dict.fromkeys(agent["agent_id"] for agent in all_agents)
        self._task_ids = dict.fromkeys(task["task_id"] for task in all_tasks)

        self.refresh_autocomplete()

    async def _agent_tasked_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        task = event["data"]["task"]
        self._task_ids[task["task_id"]] = None
        self.refresh_autocomplete()

    async def _agent_registered_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        agent = event["data"]
        print_success(f"New agent '{agent['name']}' ({agent['agent_id']}) checked in")

        self._agent_ids[agent["agent_id"]] = None
        self.refresh_autocomplete()

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
        self._agent_ids.pop(agent["agent_id"], None)
        for task_id in task_ids:
            self._task_ids.pop(task_id, None)
        self.refresh_autocomplete()

    # Single source of truth for this interpreter's event subscriptions, so that setup
    # and teardown can never drift apart. The asset and artifact events are subscribed
    # to by `BaseConnectedInterpreter` on behalf of every connected interpreter.
    def _get_event_handlers(self) -> dict[str, EventHandler]:
        return {
            "AGENT_REGISTERED": self._agent_registered_event_handler,
            "AGENT_TASKED": self._agent_tasked_event_handler,
            "AGENT_DELETED": self._agent_deleted_event_handler,
        }

    async def _setup_event_handlers(self) -> None:
        await self.client_session.websockets_api.subscribe_to_events(
            event_handlers=self._get_event_handlers(),
        )
        await self.client_session.websockets_api.start()

    async def _teardown_event_handlers(self) -> None:
        # Stop the message consumption loop for the websocket connection just so that
        # the action message being sent next doesn't need to go through the message
        # consumer handler loop. This is not necessary but just makes it cleaner.
        await self.client_session.websockets_api.stop()
        # Remove all relevant event handlers to prevent them from firing in other
        # interpreters.
        await self.client_session.websockets_api.unsubscribe_from_events(
            event_handlers=self._get_event_handlers(),
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
