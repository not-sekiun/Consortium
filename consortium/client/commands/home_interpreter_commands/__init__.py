from consortium.client.commands.home_interpreter_commands.client_session_info import (
    ClientSessionInfoCommand,
)
from consortium.client.commands.home_interpreter_commands.client_session_interact import (
    InteractClientSessionCommand,
)
from consortium.client.commands.home_interpreter_commands.connect import ConnectCommand
from consortium.client.commands.home_interpreter_commands.disconnect import (
    DisconnectCommand,
)
from consortium.client.commands.home_interpreter_commands.list_client_sessions import (
    ListClientSessionsCommand,
)
from consortium.client.commands.home_interpreter_commands.redescribe_client_session import (
    RedescribeClientSessionCommand,
)
from consortium.client.commands.home_interpreter_commands.rename_client_session import (
    RenameClientSessionCommand,
)

HOME_INTERPRETER_COMMANDS = [
    ConnectCommand(),
    DisconnectCommand(),
    ClientSessionInfoCommand(),
    InteractClientSessionCommand(),
    ListClientSessionsCommand(),
    RedescribeClientSessionCommand(),
    RenameClientSessionCommand(),
]
