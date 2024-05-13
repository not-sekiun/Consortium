from copy import deepcopy
from typing import Any

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.generators import GeneratorsCommand
from consortium.client.commands.use_agent_template_interpreter_commands.create_generator import (
    CreateGeneratorCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.info_agent_template import (
    InfoAgentTemplateCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.info_agent_template_option import (
    InfoAgentTemplateOptionsCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.list_options_agent_template import (
    ListOptionsAgentTemplateCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.reset_agent_template_option import (
    ResetAgentTemplateOptionCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.set_agent_template_option import (
    SetAgentTemplateOptionCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.unset_agent_template_option import (
    UnsetAgentTemplateOptionCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.use_agent_template import (
    UseAgentTemplateCommand,
)
from consortium.client.interpreters.generators_interpreter import (
    GENERATORS_INTERPRETER_COMMANDS,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi


class UseAgentTemplateInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_connection: ClientConnection,
        agent_template: dict[str, Any],
    ):
        use_agent_generator_interpreter_commands = [
            *[
                command
                for command in GENERATORS_INTERPRETER_COMMANDS
                if command.name not in ("info_agent_template", "use_agent_template")
            ],
            # Add back in the generators command since it's removed in the
            # GENERATORS_INTERPRETER_COMMANDS command list. This allows us to switch out
            # of the context of this specific agent template.
            GeneratorsCommand(),
            ListOptionsAgentTemplateCommand(),
            InfoAgentTemplateOptionsCommand(),
            SetAgentTemplateOptionCommand(),
            ResetAgentTemplateOptionCommand(),
            UnsetAgentTemplateOptionCommand(),
            CreateGeneratorCommand(),
            InfoAgentTemplateCommand(),
            UseAgentTemplateCommand(),
        ]
        # Add a "value" key to the options to store the current value of the
        # option.
        for option in agent_template["options"].values():
            # While technically not necessary since setting current_value overwrites the
            # value in that key, it's good practice to make a deep copy of the
            # default_value key.
            option["value"] = deepcopy(option["default_value"])
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    f"[bold white]Consortium ([bold green]Generators[bold white]: "
                    f'[bold green]"{agent_template["name"]}" '
                    f"({agent_template["agent_template_id"]})[bold white]) > ",
                ),
            ),
            commands=use_agent_generator_interpreter_commands,
            client_connection=client_connection,
            additional_environment_variables={
                "agent_template": agent_template,
            },
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
        # This environment variable is initialized in on_enter_interpreter().
        agent_template = self.environment["agent_template"]

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
                "redescribe_generator",
                "rename_generator",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {option_name: None for option_name in agent_template["options"]}
            for command in [
                "info_agent_template_option",
                "set_agent_template_option",
                "reset_agent_template_option",
                "unset_agent_template_option",
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
