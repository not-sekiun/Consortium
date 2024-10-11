from consortium.client.commands.agents_interpreter_commands.info_agent import (
    InfoAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.interact_agent import (
    InteractAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_agents import (
    ListAgentsCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_results import (
    ListResultsCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_tasks import (
    ListTasksCommand,
)

AGENTS_INTERPRETER_COMMANDS = [
    ListAgentsCommand(),
    InfoAgentCommand(),
    InteractAgentCommand(),
    ListTasksCommand(),
    ListResultsCommand(),
]
