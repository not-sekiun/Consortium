from typing import Union

import consortium_old.core.client.commands.global_commands.agents as agents
import consortium_old.core.client.commands.global_commands.home as home
import consortium_old.core.client.commands.global_commands.listeners as listeners
import consortium_old.utils.standard_io.return_color as return_color
from consortium_old.core.client.base_classes.base_interpreter import BaseInterpreter
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST


class GeneratorInterpreter(BaseInterpreter):
    def __init__(
        self,
        client: "Client",
        remote_server: Union[None, ClientREST],
        client_database: ClientDatabase,
    ):
        super().__init__(
            return_color.color_white("Consortium (", bold=True)
            + return_color.color_green("Generator", bold=True)
            + return_color.color_white(") > ", bold=True),
            [home.GlobalCommand(), listeners.GlobalCommand(), agents.GlobalCommand()],
            client,
            remote_server,
            client_database,
        )
