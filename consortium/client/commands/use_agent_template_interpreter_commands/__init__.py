from consortium.client.commands.use_agent_template_interpreter_commands.agent_template import (
    AgentTemplateCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_describe import (
    AgentTemplateDescribeCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_name import (
    AgentTemplateNameCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_option import (
    AgentTemplateOptionCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_reset_option import (
    AgentTemplateResetOptionCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_set_option import (
    AgentTemplateSetOptionCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_unset_option import (
    AgentTemplateUnsetOptionCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_use import (
    AgentTemplateUseCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.generator_create import (
    GeneratorCreateCommand,
)

USE_AGENT_TEMPLATE_INTERPRETER_COMMANDS = [
    GeneratorCreateCommand(),
    AgentTemplateCommand(),
    AgentTemplateDescribeCommand(),
    AgentTemplateNameCommand(),
    AgentTemplateOptionCommand(),
    AgentTemplateResetOptionCommand(),
    AgentTemplateSetOptionCommand(),
    AgentTemplateUnsetOptionCommand(),
    AgentTemplateUseCommand(),
]
