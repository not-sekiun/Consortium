from consortium.client.commands.agents_interpreter_commands.agent_delete import (
    AgentDeleteCommand,
)
from consortium.client.commands.agents_interpreter_commands.agent_info import (
    AgentInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.agent_interact import (
    AgentInteractCommand,
)
from consortium.client.commands.agents_interpreter_commands.agent_list import (
    AgentListCommand,
)
from consortium.client.commands.agents_interpreter_commands.agent_redescribe import (
    AgentRedescribeCommand,
)
from consortium.client.commands.agents_interpreter_commands.agent_rename import (
    AgentRenameCommand,
)
from consortium.client.commands.agents_interpreter_commands.agent_task import (
    TaskCommand,
)

AGENTS_INTERPRETER_COMMANDS = [
    AgentInfoCommand(),
    AgentInteractCommand(),
    AgentListCommand(),
    TaskCommand(),
    AgentRedescribeCommand(),
    AgentRenameCommand(),
    AgentDeleteCommand(),
]
