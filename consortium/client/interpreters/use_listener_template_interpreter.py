from copy import deepcopy

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_connection import ClientConnection
from consortium.client.commands.use_listener_template_interpreter_commands.create_listener import (
    CreateListenerCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.info_listener_template import (
    InfoListenerTemplateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.info_listener_template_option import (
    InfoListenerTemplateOptionsCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.list_options_listener_template import (
    ListOptionsListenerTemplateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.set_listener_template_option import (
    SetListenerTemplateOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.use_listener import (
    UseListenerCommand,
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
        listener_template_id: str,
        listener_template_name: str,
    ):
        use_listener_interpreter_commands = [
            *[
                command
                for command in LISTENERS_INTERPRETER_COMMANDS
                if command.name not in ("info_listener_template",)
            ],
            ListOptionsListenerTemplateCommand(),
            UseListenerCommand(),
            InfoListenerTemplateOptionsCommand(),
            SetListenerTemplateOptionCommand(),
            CreateListenerCommand(),
            InfoListenerTemplateCommand(),
        ]
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    f"[bold white]Consortium ([bold blue]Listeners[bold white]: "
                    f'[bold blue]"{listener_template_name}" '
                    f"({listener_template_id})[bold white]) > ",
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

        nested_completer_dict["start_listener"] = {
            listener["listener_id"]: None for listener in all_listeners
        }
        nested_completer_dict["stop_listener"] = {
            listener["listener_id"]: None for listener in all_listeners
        }
        nested_completer_dict["cancel_listener"] = {
            listener["listener_id"]: None for listener in all_listeners
        }
        nested_completer_dict["info_listener"] = {
            listener["listener_id"]: None for listener in all_listeners
        }
        nested_completer_dict["info_listener_template"] = {
            listener_template["listener_template_id"]: None
            for listener_template in all_listener_templates
        }
        nested_completer_dict["use_listener_template"] = {
            listener_template["listener_template_id"]: None
            for listener_template in all_listener_templates
        }
        nested_completer_dict["set_listener_parameter"] = {
            listener["listener_id"]: {
                parameter_name: None for parameter_name in listener["parameters"]
            }
            for listener in all_listeners
        }
        nested_completer_dict["rename_listener"] = {
            listener["listener_id"]: None for listener in all_listeners
        }
        nested_completer_dict["redescribe_listener"] = {
            listener["listener_id"]: None for listener in all_listeners
        }
        nested_completer_dict["set_listener_template_option"] = {
            option_name: None for option_name in listener_template["options"]
        }
        nested_completer_dict["info_listener_template_option"] = {
            option_name: None for option_name in listener_template["options"]
        }

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
