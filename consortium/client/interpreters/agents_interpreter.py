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
from consortium.client.commands.agents_interpreter_commands.list_results import (
    ListResultsCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_tasks import (
    ListTasksCommand,
)
from consortium.client.commands.agents_interpreter_commands.task import TaskCommand
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
    ListTasksCommand(),
    TaskCommand(),
    ListResultsCommand(),
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
                "list_tasks",
                "list_results",
                "task",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = {command: None for command in self.commands}

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
