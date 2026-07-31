from consortium.client.commands.listeners_interpreter_commands.listener_cancel import (
    ListenerCancelCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_delete import (
    ListenerDeleteCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_describe import (
    ListenerDescribeCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_info import (
    ListenerInfoCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_list import (
    ListenerListCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_rename import (
    ListenerRenameCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_start import (
    ListenerStartCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_stop import (
    ListenerStopCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_template import (
    ListenerTemplateCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_template_use import (
    ListenerTemplateUseCommand,
)
from consortium.client.commands.listeners_interpreter_commands.listener_update import (
    ListenerUpdateCommand,
)

LISTENERS_INTERPRETER_COMMANDS = [
    ListenerCancelCommand(),
    ListenerDeleteCommand(),
    ListenerInfoCommand(),
    ListenerTemplateCommand(),
    ListenerListCommand(),
    ListenerDescribeCommand(),
    ListenerRenameCommand(),
    ListenerUpdateCommand(),
    ListenerStartCommand(),
    ListenerStopCommand(),
    ListenerTemplateUseCommand(),
]
