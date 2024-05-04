from prompt_toolkit import ANSI

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.commands.home_interpreter_commands.connect import ConnectCommand
from consortium.client.commands.home_interpreter_commands.disconnect import (
    DisconnectCommand,
)
from consortium.client.commands.home_interpreter_commands.info_client_connection import (
    InfoClientConnectionCommand,
)
from consortium.client.commands.home_interpreter_commands.interact_client_connection import (
    InteractClientConnectionCommand,
)
from consortium.client.commands.home_interpreter_commands.list_client_connections import (
    ListClientConnectionsCommand,
)
from consortium.client.commands.home_interpreter_commands.rename_client_connection import (
    RenameClientConnectionCommand,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi


class HomeInterpreter(ClientInterpreter):
    def __init__(self, client_connection: ClientConnection):
        home_interpreter_core_commands = [
            command for command in CORE_COMMANDS if command.name != "home"
        ]
        super().__init__(
            prompt=ANSI(format_rich_text_as_ansi("[bold white]Consortium (Home) > ")),
            commands=[
                *home_interpreter_core_commands,
                InfoClientConnectionCommand(),
                ListClientConnectionsCommand(),
                RenameClientConnectionCommand(),
                ConnectCommand(),
                DisconnectCommand(),
                InteractClientConnectionCommand(),
            ],
            client_connection=client_connection,
        )
