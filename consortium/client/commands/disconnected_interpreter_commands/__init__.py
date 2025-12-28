from consortium.client.commands.disconnected_interpreter_commands.client_session_describe import (
    ClientSessionDescribeCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.client_session_disconnect import (
    ClientSessionDisconnectCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.client_session_info import (
    ClientSessionInfoCommand,
)
from consortium.client.commands.disconnected_interpreter_commands.client_session_rename import (
    ClientSessionRenameCommand,
)

DISCONNECTED_INTERPRETER_COMMANDS = [
    ClientSessionDisconnectCommand(),
    ClientSessionInfoCommand(),
    ClientSessionDescribeCommand(),
    ClientSessionRenameCommand(),
]
