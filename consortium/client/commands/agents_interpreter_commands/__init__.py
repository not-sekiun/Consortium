from consortium.client.commands.agents_interpreter_commands.agent_describe import (
    AgentDescribeCommand,
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
from consortium.client.commands.agents_interpreter_commands.agent_rename import (
    AgentRenameCommand,
)
from consortium.client.commands.agents_interpreter_commands.asset_download import (
    AssetDownloadCommand,
)
from consortium.client.commands.agents_interpreter_commands.asset_info import (
    AssetInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.asset_list import (
    AssetListCommand,
)
from consortium.client.commands.agents_interpreter_commands.asset_upload import (
    AssetUploadCommand,
)
from consortium.client.commands.agents_interpreter_commands.result_info import (
    ResultInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.result_list import (
    ResultListCommand,
)
from consortium.client.commands.agents_interpreter_commands.task_info import (
    TaskInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.task_list import (
    TaskListCommand,
)

AGENTS_INTERPRETER_COMMANDS = [
    AssetDownloadCommand(),
    AgentInfoCommand(),
    AssetInfoCommand(),
    ResultInfoCommand(),
    TaskInfoCommand(),
    AgentInteractCommand(),
    AgentListCommand(),
    AssetListCommand(),
    ResultListCommand(),
    TaskListCommand(),
    AgentDescribeCommand(),
    AgentRenameCommand(),
    AssetUploadCommand(),
]
