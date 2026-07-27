from consortium.client.commands.resource_management_commands.artifact import (
    ArtifactCommand,
)
from consortium.client.commands.resource_management_commands.asset import (
    AssetCommand,
)
from consortium.client.commands.resource_management_commands.payload import (
    PayloadCommand,
)

# Repository resources (assets, artifacts and payloads) are server wide rather than
# scoped to any one interpreter, so these commands are registered by every connected
# interpreter in the same way the core commands are.
RESOURCE_MANAGEMENT_COMMANDS = [
    AssetCommand(),
    ArtifactCommand(),
    PayloadCommand(),
]
