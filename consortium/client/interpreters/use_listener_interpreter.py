from typing import Union

import consortium_old.core.client.commands.global_commands.agents as agents
import consortium_old.core.client.commands.global_commands.generator as generator
import consortium_old.core.client.commands.global_commands.home as home
import consortium_old.core.client.commands.global_commands.listeners as listeners
import consortium_old.core.client.commands.listeners_interpreter_commands.use_listener as use_listener
import consortium_old.core.client.commands.use_listener_interpreter_commands.list_listener_options as list_listener_options
import consortium_old.core.client.commands.use_listener_interpreter_commands.reset_listener_options as reset_listener_options
import consortium_old.utils.standard_io.return_color as return_color
from consortium_old.core.client.base_classes.base_interpreter import BaseInterpreter
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST


class UseListenerInterpreter(BaseInterpreter):
    @classmethod
    async def init(
        cls,
        client: "Client",
        remote_server: Union[None, ClientREST],
        client_database: ClientDatabase,
        listener_template_id: int,
    ) -> "UseListenerInterpreter":
        # listener_template_id is guaranteed to be valid upon running this interpreter
        listener_templates_response = await remote_server.get_listener_templates()
        listener_template_options = await remote_server.get_listener_template_options(
            listener_template_id,
        )
        for listener_template_entry in listener_templates_response[
            "listener_templates"
        ]:
            if listener_template_entry["listener_template_id"] == listener_template_id:
                self = cls(
                    return_color.color_white("Consortium (", bold=True)
                    + return_color.color_blue(
                        f"Listeners: {listener_template_entry['name']}",
                        bold=True,
                    )
                    + return_color.color_white(") > ", bold=True),
                    [
                        home.GlobalCommand(),
                        agents.GlobalCommand(),
                        generator.GlobalCommand(),
                        listeners.GlobalCommand(),
                        list_listener_options.UseListenerCommand(),
                        use_listener.ListenerCommand(),
                        reset_listener_options.UseListenerCommand(),
                    ],
                    client,
                    remote_server,
                    client_database,
                )
                self.listener_template_id = listener_template_id
                self.listener_template_options = listener_template_options[
                    "listener_template_options"
                ]
                return self
