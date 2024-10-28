from consortium.client.commands.agents_interpreter_commands.download_asset import (
    DownloadAssetCommand,
)
from consortium.client.commands.agents_interpreter_commands.info_agent import (
    InfoAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.info_asset import (
    InfoAssetCommand,
)
from consortium.client.commands.agents_interpreter_commands.info_result import (
    InfoResultCommand,
)
from consortium.client.commands.agents_interpreter_commands.info_task import (
    InfoTaskCommand,
)
from consortium.client.commands.agents_interpreter_commands.interact_agent import (
    InteractAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_agents import (
    ListAgentsCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_assets import (
    ListAssetsCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_results import (
    ListResultsCommand,
)
from consortium.client.commands.agents_interpreter_commands.list_tasks import (
    ListTasksCommand,
)
from consortium.client.commands.agents_interpreter_commands.redescribe_agent import (
    RedescribeAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.rename_agent import (
    RenameAgentCommand,
)
from consortium.client.commands.agents_interpreter_commands.upload_asset import (
    UploadAssetCommand,
)

AGENTS_INTERPRETER_COMMANDS = [
    DownloadAssetCommand(),
    InfoAgentCommand(),
    InfoAssetCommand(),
    InfoResultCommand(),
    InfoTaskCommand(),
    InteractAgentCommand(),
    ListAgentsCommand(),
    ListAssetsCommand(),
    ListResultsCommand(),
    ListTasksCommand(),
    RedescribeAgentCommand(),
    RenameAgentCommand(),
    UploadAssetCommand(),
]
