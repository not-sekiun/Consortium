import pathlib
import zlib
from typing import TYPE_CHECKING

from consortium.framework.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
)
from consortium.framework.options import SingleValueOption

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent


class DownloadCapability(BaseAgentCapability):
    name = "download"
    description = "Download a file or directory from the agent."
    authors = {"Sekiun (github.com/not-sekiun)"}
    is_atomic = True
    options = {
        SingleValueOption(
            name="source",
            description="Path to the file or directory to download.",
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="destination",
            description="Local path to save the download. Defaults to current directory.",
            required=False,
            value_type=str,
        ),
        SingleValueOption(
            name="recursive",
            description="Download directory contents recursively. Ignored for files.",
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="chunk_size",
            description="Chunk size in bytes. Larger values improve speed but use more memory.",
            required=False,
            value_type=int,
            default_value=1000000,
            greater_than_or_equal_to=1,
        ),
        SingleValueOption(
            name="ignore_empty_dirs",
            description="Skip empty directories during download.",
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="compression_level",
            description="Zlib compression level (0-9). Higher values compress more.",
            required=False,
            value_type=int,
            default_value=5,
            greater_than_or_equal_to=0,
            less_than_or_equal_to=9,
        ),
        SingleValueOption(
            name="expand",
            description="Expand environment variables in source path.",
            required=False,
            value_type=bool,
            default_value=False,
        ),
    }

    async def execute(
        self,
        agent: Agent,
        task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel:
        # Remove `destination` argument before sending task because it is not needed by
        # the agent
        task_message.arguments.pop("destination")
        header = await self.send_and_recv_from_agent(
            task_message=task_message,
        )

        print(header)

        # Return the failure message if the download could not be initiated
        if not header.success:
            return header

        if header.data["type"] == "file":  # Handle file download
            filename = pathlib.Path(header.data["path"]).name
            while True:
                result = await self.recv_from_agent()
                print(result)
                if not result.success:
                    # Return failure message and stop download prematurely
                    return result

                if result.data["type"] == "end_of_file":
                    # Finished downloading file, return single message indicating
                    # success
                    return AgentResultMessageModel(
                        task_id=task_message.task_id,
                        success=True,
                        message=f"Finished downloading file {filename}",
                    )
                # `result.data["type"] == "file"` Process chunks
                chunk = zlib.decompress(result.payload.data)
                print(chunk)
        else:  # `header.data["type"] == "directory"`. Handle directory download
            directory_path = pathlib.Path(header.data["path"]).name
            while True:
                result = await self.recv_from_agent()
                print(result)
                if not result.success:
                    # Return failure message and stop download prematurely
                    return result

                if result.data["type"] == "end_of_directory":
                    # Finished downloading directory, return single message indicating
                    # success
                    return AgentResultMessageModel(
                        task_id=task_message.task_id,
                        success=True,
                        message=f"Finished downloading directory {directory_path}",
                    )
                elif result.data["type"] == "directory":  # Create new directory
                    continue
                elif result.data["type"] == "end_of_file":  # Finished a file
                    continue
                # `result.data["type"] == "file"` Process chunks
                chunk = zlib.decompress(result.payload.data)
                print(chunk)
