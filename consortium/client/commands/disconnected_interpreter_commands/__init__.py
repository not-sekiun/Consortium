from consortium.client.commands.disconnected_interpreter_commands.disconnect import (
    DisconnectCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.info_client_session import (
    ClientSessionInfoCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.redescribe_client_session import (
    RedescribeClientSessionCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.rename_client_session import (
    RenameClientSessionCommand,
)

DISCONNECTED_INTERPRETER_COMMANDS = [
    DisconnectCommand(),
    ClientSessionInfoCommand(),
    RedescribeClientSessionCommand(),
    RenameClientSessionCommand(),
]
