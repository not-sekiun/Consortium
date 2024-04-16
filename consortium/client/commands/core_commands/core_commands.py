from consortium.client.commands.core_commands.agents import AgentsCommand
from consortium.client.commands.core_commands.banner import BannerCommand
from consortium.client.commands.core_commands.clear import ClearCommand
from consortium.client.commands.core_commands.exit import ExitCommand
from consortium.client.commands.core_commands.generators import GeneratorsCommand
from consortium.client.commands.core_commands.help import HelpCommand
from consortium.client.commands.core_commands.home import HomeCommand
from consortium.client.commands.core_commands.listeners import ListenersCommand

# This constant holds the core commands that are shared between all interpreters to
# reduce code duplication and make adding core commands more straight forward.
CORE_COMMANDS = [
    ExitCommand(),
    HelpCommand(),
    ClearCommand(),
    AgentsCommand(),
    GeneratorsCommand(),
    ListenersCommand(),
    HomeCommand(),
    BannerCommand(),
]
