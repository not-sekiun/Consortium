from typing import Any

from prompt_toolkit import ANSI

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.agents import AgentsCommand
from consortium.client.interpreters.agents_interpreter import (
    AGENTS_INTERPRETER_COMMANDS,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
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
                if command.name not in ("info_agent", "interact_agent")
            ],
            # Add back in the agents command since it's removed in the
            # AGENTS_INTERPRETER_COMMANDS command list.
            AgentsCommand(),
        ]
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    f"[bold white]Consortium ([bold blue]Listeners[bold white]: "
                    f'[bold blue]"{agent["name"]}" '
                    f"({agent["agent_id"]})[bold white]) > ",
                ),
            ),
            commands=interact_agent_interpreter_commands,
            client_connection=client_connection,
            additional_environment_variables={
                "agent": agent,
            },
        )
