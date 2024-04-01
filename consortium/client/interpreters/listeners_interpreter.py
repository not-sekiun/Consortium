from typing import Union

import consortium_old.core.client.commands.global_commands.agents as agents
import consortium_old.core.client.commands.global_commands.generator as generator
import consortium_old.core.client.commands.global_commands.home as home
import consortium_old.core.client.commands.listeners_interpreter_commands.info_listener as info_listener
import consortium_old.core.client.commands.listeners_interpreter_commands.info_listener_template as info_listener_template
import consortium_old.core.client.commands.listeners_interpreter_commands.list_listener_templates as list_listener_templates
import consortium_old.core.client.commands.listeners_interpreter_commands.list_listeners as list_listeners
import consortium_old.core.client.commands.listeners_interpreter_commands.use_listener as use_listener
import consortium_old.utils.standard_io.return_color as return_color
from consortium_old.core.client.base_classes.base_interpreter import BaseInterpreter
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST


class ListenersInterpreter(BaseInterpreter):
    def __init__(
        self,
        client: "Client",
        remote_server: Union[None, ClientREST],
        client_database: ClientDatabase,
    ):
        super().__init__(
            return_color.color_white("Consortium (", bold=True)
            + return_color.color_blue("Listeners", bold=True)
            + return_color.color_white(") > ", bold=True),
            [
                home.GlobalCommand(),
                agents.GlobalCommand(),
                generator.GlobalCommand(),
                list_listeners.ListenerCommand(),
                list_listener_templates.ListenerCommand(),
                info_listener.ListenerCommand(),
                info_listener_template.ListenerCommand(),
                use_listener.ListenerCommand(),
            ],
            client,
            remote_server,
            client_database,
        )
