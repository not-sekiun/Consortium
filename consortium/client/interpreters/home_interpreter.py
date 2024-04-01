import consortium_old.core.client.commands.global_commands.agents as agents
import consortium_old.core.client.commands.global_commands.generator as generator
import consortium_old.core.client.commands.global_commands.listeners as listeners
import consortium_old.core.client.commands.home_interpreter_commands.connect as connect
import consortium_old.core.client.commands.home_interpreter_commands.disconnect as disconnect
import consortium_old.core.client.commands.home_interpreter_commands.info_server as info_server
import consortium_old.core.client.commands.home_interpreter_commands.interact_server as interact_server
import consortium_old.core.client.commands.home_interpreter_commands.list_servers as list_servers
import consortium_old.utils.standard_io.return_color as return_color
from consortium_old.core.client.base_classes.base_interpreter import BaseInterpreter
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST


class HomeInterpreter(BaseInterpreter):
    def __init__(
        self,
        client: "Client",
        remote_server: ClientREST,
        client_database: ClientDatabase,
    ):
        super().__init__(
            return_color.color_white("Consortium (Home) > ", bold=True),
            [
                listeners.GlobalCommand(),
                agents.GlobalCommand(),
                generator.GlobalCommand(),
                info_server.HomeCommand(),
                disconnect.HomeCommand(),
                connect.HomeCommand(),
                interact_server.HomeCommand(),
                list_servers.HomeCommand(),
            ],
            client,
            remote_server,
            client_database,
        )
