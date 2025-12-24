from consortium.client.commands.agents_interpreter_commands.agents_list import (
    AgentsListCommand,
)
from consortium.client.commands.agents_interpreter_commands.download_asset import (
    DownloadAssetCommand,
)
from consortium.client.commands.agents_interpreter_commands.info_agent import (
    InfoAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.info_asset import (
    InfoAssetCommand,
)
from consortium.client.commands.agents_interpreter_commands.interact_agent import (
    InteractAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_assets import (
    ListAssetsCommand,
)
from consortium.client.commands.agents_interpreter_commands.redescribe_agent import (
    RedescribeAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.rename_agent import (
    RenameAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.result_info import (
    ResultInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.results_list import (
    ResultsListCommand,
)
from consortium.client.commands.agents_interpreter_commands.task_info import (
    TaskInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.tasks_list import (
    TasksListCommand,
)
from consortium.client.commands.agents_interpreter_commands.upload_asset import (
    UploadAssetCommand,
)

AGENTS_INTERPRETER_COMMANDS = [
    DownloadAssetCommand(),
    InfoAgentCommand(),
    InfoAssetCommand(),
    ResultInfoCommand(),
    TaskInfoCommand(),
    InteractAgentCommand(),
    AgentsListCommand(),
    ListAssetsCommand(),
    ResultsListCommand(),
    TasksListCommand(),
    RedescribeAgentCommand(),
    RenameAgentCommand(),
    UploadAssetCommand(),
]
