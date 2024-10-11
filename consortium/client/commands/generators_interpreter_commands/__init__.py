from consortium.client.commands.generators_interpreter_commands.cancel_generator import (
    CancelGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.delete_generator import (
    DeleteGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.info_agent_template import (
    InfoAgentTemplateCommand,
)
from consortium.client.commands.generators_interpreter_commands.info_generator import (
    InfoGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.list_agent_templates import (
    ListAgentTemplatesCommand,
)
from consortium.client.commands.generators_interpreter_commands.list_generators import (
    ListGeneratorsCommand,
)
from consortium.client.commands.generators_interpreter_commands.redescribe_generator import (
    RedescribeGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.rename_generator import (
    RenameGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.set_generator_parameter import (
    SetGeneratorParameterCommand,
)
from consortium.client.commands.generators_interpreter_commands.start_generator import (
    StartGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.stop_generator import (
    StopGeneratorCommand,
)
from consortium.client.commands.generators_interpreter_commands.unset_generator_parameter import (
    UnsetGeneratorParameterCommand,
)
from consortium.client.commands.generators_interpreter_commands.use_agent_template import (
    UseAgentTemplateCommand,
)

GENERATORS_INTERPRETER_COMMANDS = [
    CancelGeneratorCommand(),
    DeleteGeneratorCommand(),
    InfoAgentTemplateCommand(),
    InfoGeneratorCommand(),
    ListAgentTemplatesCommand(),
    ListGeneratorsCommand(),
    RedescribeGeneratorCommand(),
    RenameGeneratorCommand(),
    SetGeneratorParameterCommand(),
    StartGeneratorCommand(),
    StopGeneratorCommand(),
    UnsetGeneratorParameterCommand(),
    UseAgentTemplateCommand(),
]
