from consortium.client.client_session import ClientSession
from consortium.client.commands.global_commands.agents import AgentsCommand
from consortium.client.commands.global_commands.alias import AliasCommand
from consortium.client.commands.global_commands.banner import BannerCommand
from consortium.client.commands.global_commands.clear import ClearCommand
from consortium.client.commands.global_commands.exit import ExitCommand
from consortium.client.commands.global_commands.generators import GeneratorsCommand
from consortium.client.commands.global_commands.help import HelpCommand
from consortium.client.commands.global_commands.listeners import ListenersCommand
from consortium.client.commands.global_commands.local import LocalCommand
from consortium.client.commands.global_commands.resource import ResourceCommand
from consortium.client.commands.home_interpreter_commands.connect import ConnectCommand
from consortium.client.commands.home_interpreter_commands.disconnect import (
    DisconnectCommand,
)
from consortium.client.commands.home_interpreter_commands.info_client_session import (
    InfoClientSessionCommand,
)
from consortium.client.commands.home_interpreter_commands.interact_client_session import (
    InteractClientSessionCommand,
)
from consortium.client.commands.home_interpreter_commands.list_client_sessions import (
    ListClientSessionsCommand,
)
from consortium.client.commands.home_interpreter_commands.rename_client_session import (
    RenameClientSessionCommand,
)
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.utils.standard_io_utils import color_white


class HomeInterpreter(BaseInterpreter):
    def __init__(self, client_session: ClientSession | None = None):
        super().__init__(
            prompt=color_white("Consortium (Home) > ", bold=True),
            commands=[
                AgentsCommand(),
                AliasCommand(),
                BannerCommand(),
                ClearCommand(),
                ExitCommand(),
                GeneratorsCommand(),
                HelpCommand(),
                ListenersCommand(),
                LocalCommand(),
                ResourceCommand(),
                InteractClientSessionCommand(),
                DisconnectCommand(),
                ConnectCommand(),
                ListClientSessionsCommand(),
                InfoClientSessionCommand(),
                RenameClientSessionCommand(),
            ],
            client_session=client_session,
        )
