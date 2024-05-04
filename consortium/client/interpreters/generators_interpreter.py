from copy import deepcopy

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.commands.generators_interpreter_commands.cancel_generator import (
    CancelGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.info_agent_template import (
    InfoAgentTemplateCommand,
)
from consortium.client.commands.generators_interpreter_commands.info_generators import (
    InfoGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.list_agent_templates import (
    ListAgentTemplatesCommand,
)
from consortium.client.commands.generators_interpreter_commands.list_generators import (
    ListGeneratorsCommand,
)
from consortium.client.commands.generators_interpreter_commands.start_generator import (
    StartGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.stop_generator import (
    StopGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.use_agent_template import (
    UseAgentTemplateCommand,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

GENERATORS_INTERPRETER_COMMANDS = [
    *[command for command in CORE_COMMANDS if command.name != "generators"],
    ListAgentTemplatesCommand(),
    InfoAgentTemplateCommand(),
    UseAgentTemplateCommand(),
    ListGeneratorsCommand(),
    StartGeneratorCommand(),
    StopGeneratorCommand(),
    CancelGeneratorCommand(),
    InfoGeneratorCommand(),
]


class GeneratorsInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_connection: ClientConnection,
    ):
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    "[bold white]Consortium ([bold green]Generators[bold white]) > ",
                ),
            ),
            commands=GENERATORS_INTERPRETER_COMMANDS,
            client_connection=client_connection,
        )

    async def on_interpreter_loop(self) -> None:
        # TODO: Listen for events on a websocket to intelligently know when to update
        #  the completer rather than updating it on each interpreter loop which adds
        #  a lot of unnecessary traffic.
        all_agent_templates = await self.environment[
            "client_connection"
        ].get_all_agent_templates()
        all_agent_generators = await self.environment[
            "client_connection"
        ].get_all_agent_generators()

        generators_interpreter_completer_dict = deepcopy(
            self.prompt_session.completer.options,
        )

        generators_interpreter_completer_dict["info_agent_template"] = {
            agent_template["agent_template_id"]: None
            for agent_template in all_agent_templates
        }
        generators_interpreter_completer_dict["info_generator"] = {
            agent_generator["agent_generator_id"]: None
            for agent_generator in all_agent_generators
        }
        generators_interpreter_completer_dict["use_agent_template"] = {
            agent_template["agent_template_id"]: None
            for agent_template in all_agent_templates
        }
        generators_interpreter_completer_dict["start_generator"] = {
            agent_generator["agent_generator_id"]: None
            for agent_generator in all_agent_generators
        }
        generators_interpreter_completer_dict["stop_generator"] = {
            agent_generator["agent_generator_id"]: None
            for agent_generator in all_agent_generators
        }
        generators_interpreter_completer_dict["cancel_generator"] = {
            agent_generator["agent_generator_id"]: None
            for agent_generator in all_agent_generators
        }

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            generators_interpreter_completer_dict,
        )
