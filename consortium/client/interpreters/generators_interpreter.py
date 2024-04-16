from prompt_toolkit import ANSI

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.formatter_utils import export_rich_text_as_ansi


class GeneratorsInterpreter(ClientInterpreter):
    def __init__(self, client_connection: ClientConnection):
        generators_commands = [
            command for command in CORE_COMMANDS if command.name != "generators"
        ]
        super().__init__(
            prompt=ANSI(
                export_rich_text_as_ansi(
                    "[bold white]Consortium ([bold green]Generators[bold white]) > ",
                ),
            ),
            commands=generators_commands,
            client_connection=client_connection,
        )
