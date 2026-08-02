from consortium.client.commands.interact_agent_interpreter_commands.agent_describe import (
    AgentDescribeCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.agent_info import (
    AgentInfoCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.agent_rename import (
    AgentRenameCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.agent_task import (
    TaskCommand,
)

INTERACT_AGENT_INTERPRETER_COMMANDS = [
    AgentInfoCommand(),
    TaskCommand(),
    AgentDescribeCommand(),
    AgentRenameCommand(),
]
