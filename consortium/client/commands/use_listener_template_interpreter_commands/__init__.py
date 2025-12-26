from consortium.client.commands.use_listener_template_interpreter_commands.info_listener_template_option import (
    InfoListenerTemplateOptionsCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.list_options_listener_template import (
    ListOptionsListenerTemplateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_create import (
    ListenerCreateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_launch import (
    ListenerLaunchCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_template_info import (
    ListenerTemplateInfoCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_template_reset_option import (
    ListenerTemplateResetOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_template_set_option import (
    ListenerTemplateSetOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_template_unset_option import (
    ListenerTemplateUnsetOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_template_use import (
    ListenerTemplateUseCommand,
)

USE_LISTENER_TEMPLATE_INTERPRETER_COMMANDS = [
    ListenerCreateCommand(),
    ListenerTemplateInfoCommand(),
    InfoListenerTemplateOptionsCommand(),
    ListenerLaunchCommand(),
    ListOptionsListenerTemplateCommand(),
    ListenerTemplateResetOptionCommand(),
    ListenerTemplateSetOptionCommand(),
    ListenerTemplateUnsetOptionCommand(),
    ListenerTemplateUseCommand(),
]
