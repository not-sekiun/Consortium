from consortium.client.commands.home_interpreter_commands.client_session_connect import (
    ConnectCommand,
)
from consortium.client.commands.home_interpreter_commands.client_session_describe import (
    ClientSessionDescribeCommand,
)
from consortium.client.commands.home_interpreter_commands.client_session_disconnect import (
    DisconnectCommand,
)
from consortium.client.commands.home_interpreter_commands.client_session_info import (
    ClientSessionInfoCommand,
)
from consortium.client.commands.home_interpreter_commands.client_session_interact import (
    InteractClientSessionCommand,
)
from consortium.client.commands.home_interpreter_commands.client_session_list import (
    ClientSessionListCommand,
)
from consortium.client.commands.home_interpreter_commands.client_session_rename import (
    ClientSessionRenameCommand,
)

HOME_INTERPRETER_COMMANDS = [
    ConnectCommand(),
    DisconnectCommand(),
    ClientSessionInfoCommand(),
    InteractClientSessionCommand(),
    ClientSessionListCommand(),
    ClientSessionDescribeCommand(),
    ClientSessionRenameCommand(),
]
