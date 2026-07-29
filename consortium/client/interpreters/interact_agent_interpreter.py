from typing import TYPE_CHECKING, Any

from prompt_toolkit import HTML
from rich.panel import Panel

from consortium.client.client_websockets_events_api import EventHandler
from consortium.client.commands.core_commands.agents import AgentsCommand
from consortium.client.commands.interact_agent_interpreter_commands import (
    INTERACT_AGENT_INTERPRETER_COMMANDS,
)

# Not imported from the interact_agents_interpreter_commands parent module since this
# command defines a special factory function that dynamically constructs commands
# objects based on externally provided data.
from consortium.client.commands.interact_agent_interpreter_commands.agent_capability_command import (
    construct_agent_capability_command,
)
from consortium.client.interpreters.agents_interpreter import (
    COMBINED_AGENTS_INTERPRETER_CORE_COMMANDS,
)
from consortium.client.models.interpreter_context_models import (
    InteractAgentInterpreterContext,
)
from consortium.client.repl_interface.autocompletes import (
    Autocomplete,
    AutocompleteResolutions,
)
from consortium.client.repl_interface.base_interpreter import (
    BaseConnectedInterpreter,
)
from consortium.client.utils.formatter_utils import (
    format_agent_task_event_type_string_with_color,
)
from consortium.client.utils.printer_utils import (
    console,
    print_info,
    print_success,
    print_warning,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class InteractAgentInterpreter(BaseConnectedInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        interpreter_context: InteractAgentInterpreterContext,
    ):
        agent = interpreter_context.agent

        # Runtime IDs the autocomplete sentinels of this interpreter's commands are
        # resolved against. Held as dictionaries so that the event handlers can add and
        # remove single IDs while preserving insertion order.
        self._agent_ids: dict[str, None] = {}
        self._task_ids: dict[str, None] = {}

        super().__init__(
            prompt=HTML(
                f"<b>Consortium (<ansired>Agents</ansired>: "
                f"<ansired>'{agent['name']}' "
                f"({agent['agent_id']})</ansired>)\n> </b>",
            ),
            commands=(
                [
                    command
                    for command in COMBINED_AGENTS_INTERPRETER_CORE_COMMANDS
                    if command.name
                    not in [
                        command.name for command in INTERACT_AGENT_INTERPRETER_COMMANDS
                    ]
                ]
                + INTERACT_AGENT_INTERPRETER_COMMANDS
                # Add back in the agents command since it's removed in the
                # AGENTS_INTERPRETER_COMMANDS command list. This allows us to switch
                # out of the context of this specific agent.
                + [AgentsCommand()]
            ),
            client_session=client_session,
            interpreter_context=interpreter_context,
        )

    async def _register_agent_capability_commands(self) -> None:
        agent_capabilities = self.interpreter_context.agent["agent_type"][
            "agent_capabilities"
        ]

        for agent_capability_name, agent_capability in agent_capabilities.items():
            # Register each agent capability as a command that can be run.
            agent_capability_command = construct_agent_capability_command(
                agent_capability=agent_capability,
            )

            # If the agent capability command name is already in the interpreter
            # commands then we need to deconflict the command name by adding a number
            # to the end of the command name.
            if agent_capability_command.name in self.commands:
                deconfliction_number = 1
                while True:
                    deconflicted_command_name = (
                        agent_capability_command.name + f"_{deconfliction_number}"
                    )
                    if deconflicted_command_name not in self.commands:
                        print_warning(
                            f"The agent capability with command "
                            f"'{agent_capability_command.name}' is conflicting with "
                            f"the command of the same name in the interpreter. The "
                            f"interpreter command name has been deconflicted to "
                            f"'{deconflicted_command_name}'.",
                        )
                        # Update the command name to the deconflicted name for both the
                        # command object and the agent capability name that is in the
                        # loop.
                        conflicted_command = self.commands.pop(
                            agent_capability_command.name,
                        )
                        conflicted_command.name = deconflicted_command_name
                        self.commands[deconflicted_command_name] = conflicted_command
                        break
                    deconfliction_number += 1

            # Note that `_register_agent_capability_commands` is called in `on_enter`
            # which in turn is called only after the interpreter has been constructed.
            # Register each agent capability command for the autocompleter.
            self.commands[agent_capability_name] = agent_capability_command
            # Also register in the context for the help command to display properly.
            self.interpreter_context.commands_info[agent_capability_name] = (
                agent_capability_command
            )

    def get_autocomplete_resolutions(self) -> AutocompleteResolutions:
        return super().get_autocomplete_resolutions() | {
            Autocomplete.AGENT_ID: self._agent_ids,
            Autocomplete.AGENT_TASK_ID: self._task_ids,
        }

    # The agent capability commands this interpreter registers dynamically carry no
    # autocompletes of their own, they are picked up by the rebuild purely by being
    # registered as commands.
    async def _initialize_autocompleter(self) -> None:
        all_agents = await self.client_session.rest_api.get_all_agents()
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

    async def _task_deleted_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        task = event["data"]
        self._task_ids.pop(task["task_id"], None)
        self.refresh_autocomplete()

    async def _agent_task_completed_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        message = event["message"]
        agent_id = event["data"]["agent_id"]
        task = event["data"]["task"]

        if (
            agent_id == self.interpreter_context.agent["agent_id"]
            and task["event_log"]["entries"]
        ):
            print_info(f"{message}")

            events_summary_lines = []
            for entry in task["event_log"]["entries"]:
                sequence = entry["sequence"]
                event_type = entry["event_type"]
                message = entry["message"]

                events_summary_lines.append(
                    f"[dim white][{sequence}][/] "
                    f"{format_agent_task_event_type_string_with_color(event_type_str=event_type)}: "
                    f"{message}"
                )

            console.print(
                Panel(
                    "\n".join(events_summary_lines),
                    title=f"Events summary ({len(task['event_log']['entries'])}/{task['event_log']['total_count']} entries displayed)",
                    title_align="left",
                    expand=False,
                )
            )

    async def _agent_registered_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        agent = event["data"]
        print_success(f"New agent '{agent['name']}' ({agent['agent_id']}) checked in")

        self._agent_ids[agent["agent_id"]] = None
        self.refresh_autocomplete()

    # Single source of truth for this interpreter's event subscriptions, so that setup
    # and teardown can never drift apart. The asset and artifact events are subscribed
    # to by `BaseConnectedInterpreter` on behalf of every connected interpreter.
    def _get_event_handlers(self) -> dict[str, EventHandler]:
        return {
            "AGENT_TASK_COMPLETED": self._agent_task_completed_event_handler,
            "AGENT_TASKED": self._agent_tasked_event_handler,
            "TASK_DELETED": self._task_deleted_event_handler,
        }

    async def _setup_event_handlers(self) -> None:
        # Register all relevant event handlers first
        await self.client_session.websockets_api.subscribe_to_events(
            event_handlers=self._get_event_handlers(),
        )
        # Start the websocket connection to listen for all registered events.
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
        await self._register_agent_capability_commands()
        await self._initialize_autocompleter()
        await self._setup_event_handlers()

    async def on_exit(self) -> None:
        # The exit command when executed will disconnect the websocket connection but
        # this method will still run so we need to first check if the client websockets
        # API connection has already been disconnected.
        if self.client_session.websockets_api.connected:
            await self._teardown_event_handlers()
