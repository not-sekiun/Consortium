from consortium.client.commands.generators_interpreter_commands.agent_template_info import (
    AgentTemplateInfoCommand,
)
from consortium.client.commands.generators_interpreter_commands.agent_template_list import (
    AgentTemplateListCommand,
)
from consortium.client.commands.generators_interpreter_commands.agent_template_use import (
    AgentTemplateUseCommand,
)
from consortium.client.commands.generators_interpreter_commands.generator_cancel import (
    GeneratorCancelCommand,
)
from consortium.client.commands.generators_interpreter_commands.generator_delete import (
    GeneratorDeleteCommand,
)
from consortium.client.commands.generators_interpreter_commands.generator_describe import (
    GeneratorDescribeCommand,
)
from consortium.client.commands.generators_interpreter_commands.generator_info import (
    GeneratorInfoCommand,
)
from consortium.client.commands.generators_interpreter_commands.generator_rename import (
    GeneratorRenameCommand,
)
from consortium.client.commands.generators_interpreter_commands.generator_start import (
    GeneratorStartCommand,
)
from consortium.client.commands.generators_interpreter_commands.generator_stop import (
    GeneratorStopCommand,
)
from consortium.client.commands.generators_interpreter_commands.generator_update import (
    GeneratorUpdateCommand,
)
from consortium.client.commands.generators_interpreter_commands.generators_list import (
    GeneratorListCommand,
)

GENERATORS_INTERPRETER_COMMANDS = [
    GeneratorCancelCommand(),
    GeneratorDeleteCommand(),
    AgentTemplateInfoCommand(),
    GeneratorInfoCommand(),
    AgentTemplateListCommand(),
    GeneratorListCommand(),
    GeneratorDescribeCommand(),
    GeneratorRenameCommand(),
    GeneratorUpdateCommand(),
    GeneratorStartCommand(),
    GeneratorStopCommand(),
    AgentTemplateUseCommand(),
]
