from consortium.client.commands.agents_interpreter_commands.task_info import (
    TaskInfoCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.agent_describe import (
    AgentDescribeCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.agent_info import (
    AgentInfoCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.agent_rename import (
    AgentRenameCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.task_list import (
    TaskListCommand,
)

INTERACT_AGENT_INTERPRETER_COMMANDS = [
    AgentInfoCommand(),
    TaskInfoCommand(),
    TaskListCommand(),
    AgentDescribeCommand(),
    AgentRenameCommand(),
]
