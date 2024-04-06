from consortium.client.client_session import ClientSession
from consortium.client.commands.global_commands.agents import AgentsCommand
from consortium.client.commands.global_commands.alias import AliasCommand
from consortium.client.commands.global_commands.banner import BannerCommand
from consortium.client.commands.global_commands.clear import ClearCommand
from consortium.client.commands.global_commands.exit import ExitCommand
from consortium.client.commands.global_commands.generators import GeneratorsCommand
from consortium.client.commands.global_commands.help import HelpCommand
from consortium.client.commands.global_commands.home import HomeCommand
from consortium.client.commands.global_commands.local import LocalCommand
from consortium.client.commands.global_commands.resource import ResourceCommand
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
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.utils.standard_io_utils import color_blue, color_white


class ListenersInterpreter(BaseInterpreter):
    def __init__(self, client_session: ClientSession | None = None):
        super().__init__(
            prompt=(
                color_white("Consortium (", bold=True)
                + color_blue("Listeners", bold=True)
                + color_white(") > ", bold=True)
            ),
            commands=[
                AgentsCommand(),
                AliasCommand(),
                BannerCommand(),
                ClearCommand(),
                ExitCommand(),
                GeneratorsCommand(),
                HelpCommand(),
                HomeCommand(),
                LocalCommand(),
                ResourceCommand(),
                ListListenerTemplatesCommand(),
                InfoListenerTemplateCommand(),
                ListListenersCommand(),
                InfoListenerCommand(),
            ],
            client_session=client_session,
        )
