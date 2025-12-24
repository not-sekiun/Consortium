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
from consortium.client.repl_interface.client_interpreter import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.printer_utils import print_info, print_warning

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class InteractAgentInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        agent: dict[str, Any],
    ):
        super().__init__(
            prompt=HTML(
                f"<b>Consortium (<ansired>Agents</ansired>: "
                f"<ansired>'{agent['name']}' "
                f"({agent['agent_id']})</ansired>) > </b>",
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
            additional_environment_variables={
                "agent": agent,
            },
        )

    async def _register_agent_capability_commands(self) -> None:
        agent_capabilities = self.environment["agent"]["agent_type"][
            "agent_capabilities"
        ]

        for agent_capability_name, agent_capability in agent_capabilities.items():
            # Register each agent capability as a command that can be run.
            agent_capability_command = construct_agent_capability_command(
                agent_capability_json_data=agent_capability,
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

            self.commands[agent_capability_name] = agent_capability_command
            # Register each agent capability command in the autocompleter.
            self.environment["commands"][agent_capability_name] = (
                agent_capability_command
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
            "result_info",
            "task_info",
            "interact_agent",
            "results_list",
            "tasks_list",
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
        nested_completer_dict["help"] = dict.fromkeys(self.commands)

        # Register each agent capability command to the autocompleter without any
        # argument completions.
        agent_capabilities = self.environment["agent"]["agent_type"][
            "agent_capabilities"
        ]
        for agent_capability_name in agent_capabilities:
            nested_completer_dict[agent_capability_name] = dict.fromkeys(self.commands)

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    # Event handler listens for specific agent events related to the current agent
    # being interacted with, namely any received agent results.
    async def _agent_result_received_event_handler(
        self,
        event: dict[str, Any],
    ) -> None:
        if event["data"]["agent_id"] == self.environment["agent"]["agent_id"]:
            result = event["data"]["result"]
            print_info(
                f"Received result with result ID '{result['result_id']}' for "
                f"task with task ID '{result['task_id']}':\n{result['message']}",
            )

    async def _setup_event_handlers(self) -> None:
        # Register all relevant event handlers first
        await self.environment["client_websockets_api_connection"].subscribe_to_event(
            event_type="AGENT_RESULT_RECEIVED",
            event_handler=self._agent_result_received_event_handler,
        )
        # Start the websocket connection to listen for all registered events.
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
            event_type="AGENT_RESULT_RECEIVED",
            event_handler=self._agent_result_received_event_handler,
        )

    async def on_enter_interpreter(self) -> None:
        await self._register_agent_capability_commands()
        await self._update_autocomplete()
        await self._setup_event_handlers()

    async def on_exit_interpreter(self) -> None:
        # The exit command when executed will disconnect the websocket connection but
        # this method will still run so we need to first check if the client websockets
        # API connection has already been disconnected.
        if self.environment["client_websockets_api_connection"].connected:
            await self._teardown_event_handlers()
