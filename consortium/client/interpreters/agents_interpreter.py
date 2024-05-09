from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.agents_interpreter_commands.info_agent import (
    InfoAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.interact_agent import (
    InteractAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_agents import (
    ListAgentsCommand,
)
from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

AGENTS_INTERPRETER_COMMANDS = [
    *[command for command in CORE_COMMANDS if command.name != "agents"],
    ListAgentsCommand(),
    InfoAgentCommand(),
    InteractAgentCommand(),
]


class AgentsInterpreter(ClientInterpreter):
    def __init__(self, client_connection: ClientConnection):
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    "[bold white]Consortium ([bold red]Agents[bold white]) > ",
                ),
            ),
            commands=AGENTS_INTERPRETER_COMMANDS,
            client_connection=client_connection,
        )

    async def on_interpreter_loop(self) -> None:
        # TODO: Listen for events on a websocket to intelligently know when to update
        #  the completer rather than updating it on each interpreter loop which adds
        #  a lot of unnecessary traffic.
        all_agents = await self.environment["client_connection"].get_all_agents()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )

        nested_completer_dict["info_agent"] = {
            agent["agent_id"]: None for agent in all_agents
        }
        nested_completer_dict["interact_agent"] = {
            agent["agent_id"]: None for agent in all_agents
        }

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
