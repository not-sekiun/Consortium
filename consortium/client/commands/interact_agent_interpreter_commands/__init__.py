from consortium.client.commands.interact_agent_interpreter_commands.info_agent import (
    InfoAgentCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.info_result import (
    InfoResultCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.info_task import (
    InfoTaskCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.list_results import (
    ListResultsCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.list_tasks import (
    ListTasksCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.redescribe_agent import (
    RedescribeAgentCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.rename_agent import (
    RenameAgentCommand,
)

INTERACT_AGENT_INTERPRETER_COMMANDS = [
    InfoAgentCommand(),
    InfoTaskCommand(),
    InfoResultCommand(),
    ListResultsCommand(),
    ListTasksCommand(),
    RedescribeAgentCommand(),
    RenameAgentCommand(),
]
