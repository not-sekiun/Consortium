from prompt_toolkit import ANSI

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.commands.generators_interpreter_commands.info_agent_template import (
    InfoAgentTemplateCommand,
)
from consortium.client.commands.generators_interpreter_commands.list_agent_templates import (
    ListAgentTemplatesCommand,
)
from consortium.client.commands.generators_interpreter_commands.list_generators import (
    ListGeneratorsCommand,
)
from consortium.client.commands.generators_interpreter_commands.use_generator import (
    UseGeneratorCommand,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.formatter_utils import export_rich_text_as_ansi

GENERATORS_INTERPRETER_COMMANDS = [
    *[command for command in CORE_COMMANDS if command.name != "generators"],
    ListAgentTemplatesCommand(),
    InfoAgentTemplateCommand(),
    UseGeneratorCommand(),
    ListGeneratorsCommand(),
]


class GeneratorsInterpreter(ClientInterpreter):
    def __init__(self, client_connection: ClientConnection):
        super().__init__(
            prompt=ANSI(
                export_rich_text_as_ansi(
                    "[bold white]Consortium ([bold green]Generators[bold white]) > ",
                ),
            ),
            commands=GENERATORS_INTERPRETER_COMMANDS,
            client_connection=client_connection,
        )
