from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

import consortium.client.client_singletons as client_singletons
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
from consortium.client.commands.home_interpreter_commands.redescribe_client_connection import (
    RedescribeClientConnectionCommand,
)
from consortium.client.commands.home_interpreter_commands.rename_client_connection import (
    RenameClientConnectionCommand,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

client_connections_service = client_singletons.client_connections_service


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
                RedescribeClientConnectionCommand(),
            ],
            client_connection=client_connection,
        )

    async def on_interpreter_loop(self) -> None:
        all_client_connections = client_connections_service.get_all_client_connections()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            nested_completer=self.prompt_session.completer,
        )

        nested_completer_dict["info_client_connection"] = {
            str(client_connection.client_connection_id): None
            for client_connection in all_client_connections
        }
        nested_completer_dict["rename_client_connection"] = {
            str(client_connection.client_connection_id): None
            for client_connection in all_client_connections
        }
        nested_completer_dict["redescribe_client_connection"] = {
            str(client_connection.client_connection_id): None
            for client_connection in all_client_connections
        }
        nested_completer_dict["disconnect"] = {
            str(client_connection.client_connection_id): None
            for client_connection in all_client_connections
        }
        nested_completer_dict["interact_client_connection"] = {
            str(client_connection.client_connection_id): None
            for client_connection in all_client_connections
        }

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
