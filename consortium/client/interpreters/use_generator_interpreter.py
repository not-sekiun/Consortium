from copy import deepcopy

from prompt_toolkit import ANSI

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.use_generator_interpreter_commands.create_generator import (
    CreateGeneratorCommand,
)
from consortium.client.commands.use_generator_interpreter_commands.info_agent_template_options import (
    InfoAgentTemplateOptionsCommand,
)
from consortium.client.commands.use_generator_interpreter_commands.list_options_agent_template import (
    ListOptionsAgentTemplateCommand,
)
from consortium.client.commands.use_generator_interpreter_commands.set_agent_template_option import (
    SetAgentTemplateOptionCommand,
)
from consortium.client.interpreters.generators_interpreter import (
    GENERATORS_INTERPRETER_COMMANDS,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.formatter_utils import export_rich_text_as_ansi


class UseGeneratorInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_connection: ClientConnection,
        agent_template_id: str,
        agent_template_name: str,
    ):
        use_agent_generator_interpreter_commands = [
            *[command for command in GENERATORS_INTERPRETER_COMMANDS],
            ListOptionsAgentTemplateCommand(),
            InfoAgentTemplateOptionsCommand(),
            SetAgentTemplateOptionCommand(),
            CreateGeneratorCommand(),
        ]
        super().__init__(
            prompt=ANSI(
                export_rich_text_as_ansi(
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
