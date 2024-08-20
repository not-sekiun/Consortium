from collections.abc import AsyncGenerator

from consortium.framework.base_agent_capability import (
    AgentCapabilityCommunicationModel,
    BaseAgentCapability,
    SupportedOS,
)
from consortium.framework.options import SingleValueOption
from consortium.server.models.agent_models import AgentMessageModel, AgentResponseModel


class DownloadCapability(BaseAgentCapability):
    name = "download"
    description = "Download a file from the agent."
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    authors = {"sekiun"}
    communication_model = AgentCapabilityCommunicationModel.LISTENER_DIRECTED_STREAMING
    arguments = {
        SingleValueOption(
            name="source",
            description=(
                "The filepath of the file or directory to download from the agent."
            ),
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="destination",
            description=(
                "The full filepath to write the downloaded file or directory to on the "
                "listener. If not provided, the file or directory will be saved in the "
                "current working directory."
            ),
            required=False,
            value_type=str,
        ),
        SingleValueOption(
            name="recursive",
            description=(
                "Whether to download the source directory and its contents "
                "recursively. If downloading is not recursive, only the files within "
                "the directory will be downloaded. This option cannot be set to true "
                "if the source is a file."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="chunk_size",
            description=(
                "Size of the chunks to use in bytes when downloading files from the "
                "agent."
            ),
            required=False,
            value_type=int,
            default_value=1024,
        ),
    }

    async def on_agent_message_sent(
        self,
        agent_message: AgentMessageModel,
    ) -> AsyncGenerator[AgentMessageModel]:
        return task

    async def on_agent_response_received(
        self,
        agent_response: AgentResponseModel,
    ) -> AsyncGenerator[AgentResponseModel]:
        return result
