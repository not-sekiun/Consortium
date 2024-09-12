from copy import deepcopy
from typing import Any

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.core_commands.listeners import ListenersCommand
from consortium.client.commands.use_listener_template_interpreter_commands.create_listener import (
    CreateListenerCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.info_listener_template import (
    InfoListenerTemplateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.info_listener_template_option import (
    InfoListenerTemplateOptionsCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.launch_listener import (
    LaunchListenerCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.list_options_listener_template import (
    ListOptionsListenerTemplateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.reset_listener_template_option import (
    ResetListenerTemplateOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.set_listener_template_option import (
    SetListenerTemplateOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.unset_listener_template_option import (
    UnsetListenerTemplateOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.use_listener_template import (
    UseListenerTemplateCommand,
)
from consortium.client.interpreters.listeners_interpreter import (
    LISTENERS_INTERPRETER_COMMANDS,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi


class UseListenerTemplateInterpreter(ClientInterpreter):
    def __init__(
        self,
        client_connection: ClientConnection,
        listener_template: dict[str, Any],
    ):
        use_listener_interpreter_commands = [
            *[
                command
                for command in LISTENERS_INTERPRETER_COMMANDS
                if command.name
                not in ("info_listener_template", "use_listener_template")
            ],
            # Add back in the listeners command since it's removed in the
            # LISTENERS_INTERPRETER_COMMANDS command list. This allows us to switch out
            # of the context of this specific listener template.
            ListenersCommand(),
            ListOptionsListenerTemplateCommand(),
            InfoListenerTemplateOptionsCommand(),
            UseListenerTemplateCommand(),
            InfoListenerTemplateCommand(),
            SetListenerTemplateOptionCommand(),
            ResetListenerTemplateOptionCommand(),
            UnsetListenerTemplateOptionCommand(),
            CreateListenerCommand(),
            LaunchListenerCommand(),
        ]
        # Add a "value" key to the options to store the current value of the
        # option.
        for option in listener_template["options"].values():
            # While technically not necessary since setting current_value overwrites the
            # value in that key, it's good practice to make a deep copy of the
            # default_value key.
            option["value"] = deepcopy(option["default_value"])
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    f"[bold white]Consortium ([bold blue]Listeners[bold white]: "
                    f'[bold blue]"{listener_template["name"]}" '
                    f"({listener_template["listener_template_id"]})[bold white]) > ",
                ),
            ),
            commands=use_listener_interpreter_commands,
            client_connection=client_connection,
            additional_environment_variables={
                "listener_template": listener_template,
            },
        )

    # TODO: Find a way for interpreters to "inherit" command completions or share
    #  common command completions. Probably could just make it a parameter
    async def on_interpreter_loop(self) -> None:
        # TODO: Listen for events on a websocket to intelligently know when to update
        #  the completer rather than updating it on each interpreter loop which adds
        #  a lot of unnecessary traffic.
        all_listeners = await self.environment["client_connection"].get_all_listeners()
        all_listener_templates = await self.environment[
            "client_connection"
        ].get_all_listener_templates()
        listener_template = self.environment["listener_template"]

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        for key, value in {
            command: {listener["listener_id"]: None for listener in all_listeners}
            for command in [
                "start_listener",
                "stop_listener",
                "cancel_listener",
                "delete_listener",
                "info_listener",
                "rename_listener",
                "redescribe_listener",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {option_name: None for option_name in listener_template["options"]}
            for command in [
                "info_listener_template_option",
                "set_listener_template_option",
                "reset_listener_template_option",
                "unset_listener_template_option",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {
                listener_template["listener_template_id"]: None
                for listener_template in all_listener_templates
            }
            for command in ["use_listener_template", "info_listener_template"]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {
                listener["listener_id"]: {
                    parameter_name: None for parameter_name in listener["parameters"]
                }
                for listener in all_listeners
            }
            for command in [
                "set_listener_parameter",
                "unset_listener_parameter",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = {command: None for command in self.commands}

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
