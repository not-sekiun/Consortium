from typing import Any

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.agents import AgentsCommand
from consortium.client.commands.interact_agent_interpreter_commands.info_agent import (
    InfoAgentCommand,
)
from consortium.client.interpreters.agents_interpreter import (
    AGENTS_INTERPRETER_COMMANDS,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi


class InteractAgentInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_connection: ClientConnection,
        agent: dict[str, Any],
    ):
        interact_agent_interpreter_commands = [
            *[
                command
                for command in AGENTS_INTERPRETER_COMMANDS
                if command.name not in ("info_agent",)
            ],
            # Add back in the agents command since it's removed in the
            # AGENTS_INTERPRETER_COMMANDS command list. This allows us to switch out of
            # the context of this specific agent.
            AgentsCommand(),
            InfoAgentCommand(),
        ]
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    f"[bold white]Consortium ([bold red]Agents[bold white]: "
                    f'[bold red]"{agent["name"]}" '
                    f"({agent["agent_id"]})[bold white]) > ",
                ),
            ),
            commands=interact_agent_interpreter_commands,
            client_connection=client_connection,
            additional_environment_variables={
                "agent": agent,
            },
        )

    # TODO: Find a way for interpreters to "inherit" command completions or share
    #  common command completions. Probably could just make it a parameter
    async def on_interpreter_loop(self) -> None:
        # TODO: Listen for events on a websocket to intelligently know when to update
        #  the completer rather than updating it on each interpreter loop which adds
        #  a lot of unnecessary traffic.
        all_agents = await self.environment["client_connection"].get_all_agents()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        for key, value in {
            command: {agent["agent_id"]: None for agent in all_agents}
            for command in [
                "info_agent",
                "interact_agent",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = {command: None for command in self.commands}

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
