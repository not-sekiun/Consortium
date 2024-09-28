from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_rest_api_connection import ClientRESTAPIConnection
from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.commands.generators_interpreter_commands.cancel_generator import (
    CancelGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.delete_generator import (
    DeleteGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.info_agent_template import (
    InfoAgentTemplateCommand,
)
from consortium.client.commands.generators_interpreter_commands.info_generator import (
    InfoGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.list_agent_templates import (
    ListAgentTemplatesCommand,
)
from consortium.client.commands.generators_interpreter_commands.list_generators import (
    ListGeneratorsCommand,
)
from consortium.client.commands.generators_interpreter_commands.redescribe_generator import (
    RedescribeGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.rename_generator import (
    RenameGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.set_generator_parameter import (
    SetGeneratorParameterCommand,
)
from consortium.client.commands.generators_interpreter_commands.start_generator import (
    StartGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.stop_generator import (
    StopGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.unset_generator_parameter import (
    UnsetGeneratorParameterCommand,
)
from consortium.client.commands.generators_interpreter_commands.use_agent_template import (
    UseAgentTemplateCommand,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

GENERATORS_INTERPRETER_COMMANDS = [
    *[command for command in CORE_COMMANDS if command.name != "generators"],
    ListAgentTemplatesCommand(),
    InfoAgentTemplateCommand(),
    UseAgentTemplateCommand(),
    InfoGeneratorCommand(),
    ListGeneratorsCommand(),
    StartGeneratorCommand(),
    StopGeneratorCommand(),
    CancelGeneratorCommand(),
    DeleteGeneratorCommand(),
    RenameGeneratorCommand(),
    RedescribeGeneratorCommand(),
    SetGeneratorParameterCommand(),
    UnsetGeneratorParameterCommand(),
]


class GeneratorsInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_connection: ClientRESTAPIConnection,
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

    # TODO: Find a way for interpreters to "inherit" command completions or share
    #  common command completions. Probably could just make it a parameter
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

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        for key, value in {
            command: {
                agent_generator["agent_generator_id"]: None
                for agent_generator in all_agent_generators
            }
            for command in [
                "start_generator",
                "stop_generator",
                "cancel_generator",
                "delete_generator",
                "info_generator",
                "rename_generator",
                "redescribe_generator",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {
                agent_template["agent_template_id"]: None
                for agent_template in all_agent_templates
            }
            for command in [
                "use_agent_template",
                "info_agent_template",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {
                agent_generator["agent_generator_id"]: {
                    parameter_name: None
                    for parameter_name in agent_generator["parameters"]
                }
                for agent_generator in all_agent_generators
            }
            for command in [
                "set_generator_parameter",
                "unset_generator_parameter",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = {command: None for command in self.commands}

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
