from consortium.client.commands.use_listener_template_interpreter_commands.listener_create import (
    ListenerCreateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_template import (
    ListenerTemplateCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_template_option import (
    ListenerTemplateOptionCommand,
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
    ListenerTemplateCommand(),
    ListenerTemplateOptionCommand(),
    ListenerTemplateResetOptionCommand(),
    ListenerTemplateSetOptionCommand(),
    ListenerTemplateUnsetOptionCommand(),
    ListenerTemplateUseCommand(),
]
