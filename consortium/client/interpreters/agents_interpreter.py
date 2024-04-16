from prompt_toolkit import ANSI

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.formatter_utils import export_rich_text_as_ansi


class AgentsInterpreter(ClientInterpreter):
    def __init__(self, client_connection: ClientConnection):
        agents_commands = [
            command for command in CORE_COMMANDS if command.name != "agents"
        ]
        super().__init__(
            prompt=ANSI(
                export_rich_text_as_ansi(
                    "[bold white]Consortium ([bold red]Agents[bold white]) > ",
                ),
            ),
            commands=agents_commands,
            client_connection=client_connection,
        )
