from prompt_toolkit import ANSI

from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.commands.listeners_interpreter_commands.info_listener import (
    InfoListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.info_listener_template import (
    InfoListenerTemplateCommand,
)
from consortium.client.commands.listeners_interpreter_commands.list_listener_templates import (
    ListListenerTemplatesCommand,
)
from consortium.client.commands.listeners_interpreter_commands.list_listeners import (
    ListListenersCommand,
)
from consortium.client.commands.listeners_interpreter_commands.start_listener import (
    StartListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.stop_listener import (
    StopListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.use_listener import (
    UseListenerCommand,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.formatter_utils import export_rich_text_as_ansi

LISTENERS_INTERPRETER_COMMANDS = [
    *[command for command in CORE_COMMANDS if command.name != "listeners"],
    ListListenerTemplatesCommand(),
    InfoListenerTemplateCommand(),
    ListListenersCommand(),
    InfoListenerCommand(),
    UseListenerCommand(),
    StartListenerCommand(),
    StopListenerCommand(),
]


class ListenersInterpreter(ClientInterpreter):
    def __init__(self, client_connection):
        super().__init__(
            prompt=ANSI(
                export_rich_text_as_ansi(
                    "[bold white]Consortium ([bold blue]Listeners[bold white]) > ",
                ),
            ),
            commands=LISTENERS_INTERPRETER_COMMANDS,
            client_connection=client_connection,
        )
