from copy import deepcopy

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_connection import ClientConnection
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
from consortium.client.commands.use_agent_template_interpreter_commands.set_agent_template_option import (
    SetAgentTemplateOptionCommand,
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
        agent_template_id: str,
        agent_template_name: str,
    ):
        use_agent_generator_interpreter_commands = [
            *[
                command
                for command in GENERATORS_INTERPRETER_COMMANDS
                if command.name not in ("info_agent_template",)
            ],
            ListOptionsAgentTemplateCommand(),
            InfoAgentTemplateOptionsCommand(),
            SetAgentTemplateOptionCommand(),
            CreateGeneratorCommand(),
            InfoAgentTemplateCommand(),
        ]
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    f"[bold white]Consortium ([bold green]Generators[bold white]: "
                    f'[bold green]"{agent_template_name}" '
                    f"({agent_template_id})[bold white]) > ",
                ),
            ),
            commands=use_agent_generator_interpreter_commands,
            client_connection=client_connection,
            additional_environment_variables={
                "agent_template_id": agent_template_id,
            },
        )

    # We can't do this __init__ because __init__ does not support async.
    async def on_enter_interpreter(self) -> None:
        # Make the request once to retrieve data from the server to avoid making the
        # request multiple times.
        agent_template = await self.environment[
            "client_connection"
        ].get_agent_template_by_agent_template_id(
            self.environment["agent_template_id"],
        )

        # Add a "value" key to the options to store the current value of the
        # option.
        for option in agent_template["options"].values():
            # While technically not necessary since setting current_value overwrites the
            # value in that key, it's good practice to make a deep copy of the
            # default_value key.
            option["value"] = deepcopy(option["default_value"])

        self.environment["agent_template"] = agent_template

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

        nested_completer_dict["info_agent_template_option"] = {
            agent_template["agent_template_id"]: None
            for agent_template in all_agent_templates
        }
        nested_completer_dict["info_generator"] = {
            agent_generator["agent_generator_id"]: None
            for agent_generator in all_agent_generators
        }
        nested_completer_dict["use_agent_template"] = {
            agent_template["agent_template_id"]: None
            for agent_template in all_agent_templates
        }
        nested_completer_dict["start_generator"] = {
            agent_generator["agent_generator_id"]: None
            for agent_generator in all_agent_generators
        }
        nested_completer_dict["stop_generator"] = {
            agent_generator["agent_generator_id"]: None
            for agent_generator in all_agent_generators
        }
        nested_completer_dict["cancel_generator"] = {
            agent_generator["agent_generator_id"]: None
            for agent_generator in all_agent_generators
        }
        nested_completer_dict["set_agent_template_option"] = {
            option_name: None for option_name in agent_template["options"]
        }
        nested_completer_dict["info_agent_template_option"] = {
            option_name: None for option_name in agent_template["options"]
        }

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
