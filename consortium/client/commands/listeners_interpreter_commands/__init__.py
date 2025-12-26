from consortium.client.commands.listeners_interpreter_commands.cancel_listener import (
    CancelListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.delete_listener import (
    DeleteListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.info_listener import (
    InfoListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.info_listener_template import (
    InfoListenerTemplateCommand,
)
from consortium.client.commands.listeners_interpreter_commands.list_listener_templates import (
    ListListenerTemplatesCommand,
)
from consortium.client.commands.listeners_interpreter_commands.list_listeners import (
    ListListenersCommand,
)
from consortium.client.commands.listeners_interpreter_commands.redescribe_listener import (
    RedescribeListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.rename_listener import (
    RenameListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.set_listener_parameter import (
    SetListenerParameterCommand,
)
from consortium.client.commands.listeners_interpreter_commands.start_listener import (
    StartCommand,
)
from consortium.client.commands.listeners_interpreter_commands.stop_listener import (
    StopListenerCommand,
)
from consortium.client.commands.listeners_interpreter_commands.unset_listener_parameter import (
    UnsetListenerParameterCommand,
)
from consortium.client.commands.listeners_interpreter_commands.use_listener_template import (
    UseListenerTemplateCommand,
)

LISTENERS_INTERPRETER_COMMANDS = [
    CancelListenerCommand(),
    DeleteListenerCommand(),
    InfoListenerCommand(),
    InfoListenerTemplateCommand(),
    ListListenerTemplatesCommand(),
    ListListenersCommand(),
    RedescribeListenerCommand(),
    RenameListenerCommand(),
    SetListenerParameterCommand(),
    StartCommand(),
    StopListenerCommand(),
    UnsetListenerParameterCommand(),
    UseListenerTemplateCommand(),
]
