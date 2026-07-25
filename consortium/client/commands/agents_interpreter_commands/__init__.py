from consortium.client.commands.agents_interpreter_commands.agent_delete import (
    AgentDeleteCommand,
)
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
from consortium.client.commands.agents_interpreter_commands.artifact_describe import (
    ArtifactDescribeCommand,
)
from consortium.client.commands.agents_interpreter_commands.artifact_download import (
    ArtifactDownloadCommand,
)
from consortium.client.commands.agents_interpreter_commands.artifact_info import (
    ArtifactInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.artifact_list import (
    ArtifactListCommand,
)
from consortium.client.commands.agents_interpreter_commands.artifact_remove import (
    ArtifactRemoveCommand,
)
from consortium.client.commands.agents_interpreter_commands.artifact_rename import (
    ArtifactRenameCommand,
)
from consortium.client.commands.agents_interpreter_commands.asset_describe import (
    AssetDescribeCommand,
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
from consortium.client.commands.agents_interpreter_commands.asset_remove import (
    AssetRemoveCommand,
)
from consortium.client.commands.agents_interpreter_commands.asset_rename import (
    AssetRenameCommand,
)
from consortium.client.commands.agents_interpreter_commands.asset_upload import (
    AssetUploadCommand,
)
from consortium.client.commands.agents_interpreter_commands.task_info import (
    TaskInfoCommand,
)
from consortium.client.commands.agents_interpreter_commands.task_list import (
    TaskListCommand,
)
from consortium.client.commands.agents_interpreter_commands.watch import (
    WatchCommand,
)

AGENTS_INTERPRETER_COMMANDS = [
    AssetDownloadCommand(),
    AgentInfoCommand(),
    AssetInfoCommand(),
    TaskInfoCommand(),
    AgentInteractCommand(),
    AgentListCommand(),
    AssetListCommand(),
    AssetRemoveCommand(),
    AssetDescribeCommand(),
    AssetRenameCommand(),
    AssetUploadCommand(),
    ArtifactDownloadCommand(),
    ArtifactInfoCommand(),
    ArtifactListCommand(),
    ArtifactRemoveCommand(),
    ArtifactDescribeCommand(),
    ArtifactRenameCommand(),
    TaskListCommand(),
    AgentDescribeCommand(),
    AgentRenameCommand(),
    AgentDeleteCommand(),
    WatchCommand(),
]
