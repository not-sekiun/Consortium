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
from consortium.client.commands.home_interpreter_commands.redescribe_client_session import (
    RedescribeClientSessionCommand,
)
from consortium.client.commands.home_interpreter_commands.rename_client_session import (
    RenameClientSessionCommand,
)

HOME_INTERPRETER_COMMANDS = [
    ConnectCommand(),
    DisconnectCommand(),
    InfoClientSessionCommand(),
    InteractClientSessionCommand(),
    ListClientSessionsCommand(),
    RedescribeClientSessionCommand(),
    RenameClientSessionCommand(),
]
