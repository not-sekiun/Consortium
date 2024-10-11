from consortium.client.commands.use_listener_template_interpreter_commands.create_listener import (
    CreateListenerCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.info_listener_template import (
    InfoListenerTemplateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.info_listener_template_option import (
    InfoListenerTemplateOptionsCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.launch_listener import (
    LaunchListenerCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.list_options_listener_template import (
    ListOptionsListenerTemplateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.reset_listener_template_option import (
    ResetListenerTemplateOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.set_listener_template_option import (
    SetListenerTemplateOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.unset_listener_template_option import (
    UnsetListenerTemplateOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.use_listener_template import (
    UseListenerTemplateCommand,
)

USE_LISTENER_TEMPLATE_INTERPRETER_COMMANDS = [
    CreateListenerCommand(),
    InfoListenerTemplateCommand(),
    InfoListenerTemplateOptionsCommand(),
    LaunchListenerCommand(),
    ListOptionsListenerTemplateCommand(),
    ResetListenerTemplateOptionCommand(),
    SetListenerTemplateOptionCommand(),
    UnsetListenerTemplateOptionCommand(),
    UseListenerTemplateCommand(),
]
