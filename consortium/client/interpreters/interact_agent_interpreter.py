from typing import TYPE_CHECKING, Any

from prompt_toolkit import HTML
from prompt_toolkit.completion import NestedCompleter

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
from consortium.client.repl_interface.base_interpreter import (
    BaseConnectedInterpreter,
)
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.printer_utils import (
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

    async def _initialize_autocompleter(self) -> None:
        all_agents = await self.client_session.rest_api.get_all_agents()
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
            "t-list",
            "rename",
            "describe",
        ]:
            nested_completer_dict[command] = agent_ids_completion

        # Register commands that take the task ID as a positional argument
        all_tasks = await self.client_session.rest_api.get_all_agent_tasks()
        for command in ["t-info", "watch"]:
            nested_completer_dict[command] = {
                task["task_id"]: None for task in all_tasks
            }

        # Register commands that take the asset ID as the first positional argument to
        # autocomplete with.
        assets_completion = {asset["resource_id"]: None for asset in all_assets}
        for command in ["as-dl", "as-info"]:
            nested_completer_dict[command] = assets_completion

        # Register the help command to autocomplete with all available commands. This
        # includes all the newly added agent capability commands that are dynamically
        # added before this method is called.
        nested_completer_dict["help"] = dict.fromkeys(self.commands)

        # Register each agent capability command to the autocompleter without any
        # argument completions.
        agent_capabilities = self.interpreter_context.agent["agent_type"][
            "agent_capabilities"
        ]
        for agent_capability_name in agent_capabilities:
            nested_completer_dict[agent_capability_name] = dict.fromkeys(self.commands)

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
        nested_completer_dict["watch"][task["task_id"]] = None
        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    async def _agent_task_completed_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        message = event["message"]
        agent_id = event["data"]["agent_id"]
        task = event["data"]["task"]

        # TODO: Prettify task printing
        if agent_id == self.interpreter_context.agent["agent_id"]:
            print_info(
                f"{message}:\n{task}",
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
            "t-list",
            "rename",
            "describe",
        ]:
            nested_completer_dict[command][agent["agent_id"]] = None
        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    async def _setup_event_handlers(self) -> None:
        # Register all relevant event handlers first
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="AGENT_TASK_COMPLETED",
            event_handler=self._agent_task_completed_event_handler,
        )
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="AGENT_TASKED",
            event_handler=self._agent_tasked_event_handler,
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
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="AGENT_TASK_COMPLETED",
            event_handler=self._agent_task_completed_event_handler,
        )
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="AGENT_TASKED",
            event_handler=self._agent_tasked_event_handler,
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
