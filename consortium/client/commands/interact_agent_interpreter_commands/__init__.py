from consortium.client.commands.agents_interpreter_commands.result_info import (
    ResultInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.task_info import (
    TaskInfoCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.info_agent import (
    InfoAgentCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.redescribe_agent import (
    RedescribeAgentCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.rename_agent import (
    RenameAgentCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.results_list import (
    ResultsListCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.tasks_list import (
    TasksListCommand,
)

INTERACT_AGENT_INTERPRETER_COMMANDS = [
    InfoAgentCommand(),
    TaskInfoCommand(),
    ResultInfoCommand(),
    ResultsListCommand(),
    TasksListCommand(),
    RedescribeAgentCommand(),
    RenameAgentCommand(),
]
