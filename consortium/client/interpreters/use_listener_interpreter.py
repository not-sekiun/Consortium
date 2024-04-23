from copy import deepcopy

from prompt_toolkit import ANSI

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.use_listener_interpreter_commands.create_listener import (
    CreateListenerCommand,
)
from consortium.client.commands.use_listener_interpreter_commands.info_listener_template_options import (
    InfoListenerTemplateOptionsCommand,
)
from consortium.client.commands.use_listener_interpreter_commands.list_options_listener_template import (
    ListOptionsListenerTemplateCommand,
)
from consortium.client.commands.use_listener_interpreter_commands.set_listener_template_option import (
    SetListenerTemplateOptionCommand,
)
from consortium.client.commands.use_listener_interpreter_commands.use_listener import (
    UseListenerCommand,
)
from consortium.client.interpreters.listeners_interpreter import (
    LISTENERS_INTERPRETER_COMMANDS,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.formatter_utils import export_rich_text_as_ansi


class UseListenerInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_connection: ClientConnection,
        listener_template_id: str,
        listener_template_name: str,
    ):
        use_listener_interpreter_commands = [
            *[command for command in LISTENERS_INTERPRETER_COMMANDS],
            ListOptionsListenerTemplateCommand(),
            UseListenerCommand(),
            InfoListenerTemplateOptionsCommand(),
            SetListenerTemplateOptionCommand(),
            CreateListenerCommand(),
        ]
        super().__init__(
            prompt=ANSI(
                export_rich_text_as_ansi(
                    f'[bold white]Consortium ([bold blue]Listeners[bold white]: [bold blue]"{listener_template_name}" ({listener_template_id})[bold white]) > ',
                ),
            ),
            commands=use_listener_interpreter_commands,
            client_connection=client_connection,
            additional_environment_variables={
                "listener_template_id": listener_template_id,
            },
        )

    # We can't do this __init__ because __init__ does not support async.
    async def on_enter_interpreter(self) -> None:
        # Make the request once to retrieve data from the server to avoid making the
        # request multiple times.
        listener_template = await self.environment[
            "client_connection"
        ].get_listener_template_by_listener_template_id(
            self.environment["listener_template_id"],
        )

        # Add a "value" key to the options to store the current value of the
        # option.
        for option in listener_template["options"].values():
            # While technically not necessary since setting current_value overwrites the
            # value in that key, it's good practice to make a deep copy of the
            # default_value key.
            option["value"] = deepcopy(option["default_value"])

        self.environment["listener_template"] = listener_template
