from typing import Union

import consortium_old.core.client.commands.home_interpreter_commands.connect as connect
import consortium_old.utils.standard_io.return_color as return_color
from consortium_old.core.client.base_classes.base_interpreter import BaseInterpreter
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST


class DisconnectedInterpreter(BaseInterpreter):
    def __init__(
        self,
        client: "Client",
        remote_server: Union[None, ClientREST],
        client_database: ClientDatabase,
    ):  # The only command this interpreter has is the connect command from the home interpreter
        super().__init__(
            return_color.color_white("Consortium (Disconnected) > ", bold=True),
            [connect.HomeCommand()],
            client,
            remote_server,
            client_database,
        )
