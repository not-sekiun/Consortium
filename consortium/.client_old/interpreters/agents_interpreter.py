from consortium.client.client_session import ClientSession
from consortium.client.commands.global_commands.alias import AliasCommand
from consortium.client.commands.global_commands.banner import BannerCommand
from consortium.client.commands.global_commands.clear import ClearCommand
from consortium.client.commands.global_commands.exit import ExitCommand
from consortium.client.commands.global_commands.generators import GeneratorsCommand
from consortium.client.commands.global_commands.help import HelpCommand
from consortium.client.commands.global_commands.home import HomeCommand
from consortium.client.commands.global_commands.listeners import ListenersCommand
from consortium.client.commands.global_commands.local import LocalCommand
from consortium.client.commands.global_commands.resource import ResourceCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.utils.standard_io_utils import color_red, color_white


class AgentsInterpreter(BaseInterpreter):
    def __init__(self):
        super().__init__(
            prompt=(
                color_white("Consortium (", bold=True)
                + color_red("Agents", bold=True)
                + color_white(") > ", bold=True)
            ),
            commands=[
                AliasCommand(),
                BannerCommand(),
                ClearCommand(),
                ExitCommand(),
                GeneratorsCommand(),
                HelpCommand(),
                HomeCommand(),
                ListenersCommand(),
                LocalCommand(),
                ResourceCommand(),
            ],
        )
