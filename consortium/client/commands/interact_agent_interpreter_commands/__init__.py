from consortium.client.commands.interact_agent_interpreter_commands.info_agent import (
    InfoAgentCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.list_results import (
    ListResultsCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.list_tasks import (
    ListTasksCommand,
)

INTERACT_AGENT_INTERPRETER_COMMANDS = [
    InfoAgentCommand(),
    ListResultsCommand(),
    ListTasksCommand(),
]
