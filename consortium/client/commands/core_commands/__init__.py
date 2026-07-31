from consortium.client.commands.core_commands.agents import AgentsCommand
from consortium.client.commands.core_commands.alias import AliasCommand
from consortium.client.commands.core_commands.banner import BannerCommand
from consortium.client.commands.core_commands.clear import ClearCommand
from consortium.client.commands.core_commands.exec import ExecCommand
from consortium.client.commands.core_commands.exit import ExitCommand
from consortium.client.commands.core_commands.generators import GeneratorsCommand
from consortium.client.commands.core_commands.help import HelpCommand
from consortium.client.commands.core_commands.home import HomeCommand
from consortium.client.commands.core_commands.listeners import ListenersCommand
from consortium.client.commands.core_commands.rc import RcCommand

CORE_COMMANDS = [
    AliasCommand(),
    ExitCommand(),
    HelpCommand(),
    ClearCommand(),
    ExecCommand(),
    AgentsCommand(),
    GeneratorsCommand(),
    ListenersCommand(),
    HomeCommand(),
    BannerCommand(),
    RcCommand(),
]
