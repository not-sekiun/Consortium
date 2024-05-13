from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

from consortium.client.commands.core_commands.core_commands import CORE_COMMANDS
from consortium.client.commands.listeners_interpreter_commands.cancel_listener import (
    CancelListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.delete_listener import (
    DeleteListenerCommand,
)
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
from consortium.client.commands.listeners_interpreter_commands.redescribe_listener import (
    RedescribeListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.rename_listener import (
    RenameListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.set_listener_parameter import (
    SetListenerParameterCommand,
)
from consortium.client.commands.listeners_interpreter_commands.start_listener import (
    StartListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.stop_listener import (
    StopListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.unset_listener_parameter import (
    UnsetListenerParameterCommand,
)
from consortium.client.commands.listeners_interpreter_commands.use_listener_template import (
    UseListenerTemplateCommand,
)
from consortium.client.objects.client_interpreter_objects import ClientInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

LISTENERS_INTERPRETER_COMMANDS = [
    *[command for command in CORE_COMMANDS if command.name != "listeners"],
    ListListenerTemplatesCommand(),
    InfoListenerTemplateCommand(),
    ListListenersCommand(),
    InfoListenerCommand(),
    UseListenerTemplateCommand(),
    StartListenerCommand(),
    StopListenerCommand(),
    CancelListenerCommand(),
    DeleteListenerCommand(),
    RenameListenerCommand(),
    RedescribeListenerCommand(),
    SetListenerParameterCommand(),
    UnsetListenerParameterCommand(),
]


class ListenersInterpreter(ClientInterpreter):
    def __init__(self, client_connection):
        super().__init__(
            prompt=ANSI(
                format_rich_text_as_ansi(
                    "[bold white]Consortium ([bold blue]Listeners[bold white]) > ",
                ),
            ),
            commands=LISTENERS_INTERPRETER_COMMANDS,
            client_connection=client_connection,
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
            command: {
                listener_template["listener_template_id"]: None
                for listener_template in all_listener_templates
            }
            for command in [
                "info_listener_template",
                "use_listener_template",
            ]
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
