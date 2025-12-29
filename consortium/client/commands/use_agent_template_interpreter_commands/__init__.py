from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_info import (
    AgentTemplateInfoCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_info_option import (
    AgentTemplateInfoOptionCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_list_option import (
    AgentTemplateListOptionCommand,
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
from consortium.client.commands.use_agent_template_interpreter_commands.generator_launch import (
    GeneratorLaunchCommand,
)

USE_AGENT_TEMPLATE_INTERPRETER_COMMANDS = [
    GeneratorCreateCommand(),
    GeneratorLaunchCommand(),
    AgentTemplateInfoCommand(),
    AgentTemplateInfoOptionCommand(),
    AgentTemplateListOptionCommand(),
    AgentTemplateResetOptionCommand(),
    AgentTemplateSetOptionCommand(),
    AgentTemplateUnsetOptionCommand(),
    AgentTemplateUseCommand(),
]
