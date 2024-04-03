from consortium.client.commands.global_commands.agents import AgentsCommand
from consortium.client.commands.global_commands.alias import AliasCommand
from consortium.client.commands.global_commands.banner import BannerCommand
from consortium.client.commands.global_commands.clear import ClearCommand
from consortium.client.commands.global_commands.exit import ExitCommand
from consortium.client.commands.global_commands.generator import GeneratorCommand
from consortium.client.commands.global_commands.help import HelpCommand
from consortium.client.commands.global_commands.home import HomeCommand
from consortium.client.commands.global_commands.listeners import ListenersCommand
from consortium.client.commands.global_commands.local import LocalCommand
from consortium.client.commands.global_commands.resource import ResourceCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.utils.standard_io_utils import color_white

home_interpreter = BaseInterpreter(
    prompt=color_white("Consortium (Home) > "),
    commands=[
        AgentsCommand(),
        AliasCommand(),
        BannerCommand(),
        ClearCommand(),
        ExitCommand(),
        GeneratorCommand(),
        HelpCommand(),
        HomeCommand(),
        ListenersCommand(),
        LocalCommand(),
        ResourceCommand(),
    ],
    client_session=None,
)
