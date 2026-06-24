import base64
import zlib
from pathlib import Path
from typing import TYPE_CHECKING

from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
)
from consortium.framework.options import SingleValueOption

if TYPE_CHECKING:
    pass


class UploadCapability(BaseAgentCapability):
    name = "upload"
    description = "Upload a file or directory to the agent"
    authors = {"Sekiun (github.com/not-sekiun)"}
    is_atomic = True
    options = {
        SingleValueOption(
            name="source",
            description="Path to the file or directory to upload.",
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="destination",
            description="Remote path to save the upload. Defaults to current directory.",
            required=False,
            value_type=str,
        ),
        SingleValueOption(
            name="recursive",
            description="Upload directory contents recursively. Ignored for files.",
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
            description="Skip empty directories during upload.",
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
            description="Expand environment variables in destination path.",
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="overwrite",
            description="Overwrite existing files at destination.",
            required=False,
            value_type=bool,
            default_value=False,
        ),
    }
    mitre_attack_techniques = {"T1105"}

    # FIXME: What the fuck is this bullshit
    async def execute(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> TaskOutputMessageModel:
        source = Path(task_message.arguments["source"])
        chunk_size = task_message.arguments["chunk_size"]
        recursive = task_message.arguments["recursive"]
        ignore_empty_dirs = task_message.arguments["ignore_empty_dirs"]
        compression_level = task_message.arguments["compression_level"]

        if not source.exists():
            return TaskOutputMessageModel(
                task_id=task_message.task_id,
                success=False,
                message=f"Failed to start upload. Path '{source}' does not exist.",
            )

        # Remove source from arguments before sending, agent doesn't need it
        task_args = {
            "destination": task_message.arguments["destination"],
            "expand": task_message.arguments["expand"],
            "overwrite": task_message.arguments["overwrite"],
        }
        task_message.arguments = task_args

        # Wait for agent to signal ready
        ready_response = await self.send_and_recv_from_agent(task_message=task_message)
        if not ready_response.success:
            return ready_response

        if ready_response.data.get("type") != "ready":
            return TaskOutputMessageModel(
                task_id=task_message.task_id,
                success=False,
                message="Agent did not signal ready for upload.",
            )

        def send_chunk(chunk_type, **kwargs):
            return self.send_upload_chunk_to_agent(
                task_id=task_message.task_id,
                chunk_data={"type": chunk_type, **kwargs},
            )

        def stream_file_chunks(file_path):
            with open(file_path, mode="rb") as file:
                while chunk := file.read(chunk_size):
                    if compression_level:
                        chunk = zlib.compress(chunk, level=compression_level)
                        send_chunk(
                            "chunk",
                            chunk=base64.b64encode(chunk).decode(),
                            compressed=True,
                        )
                    else:
                        send_chunk("chunk", chunk=base64.b64encode(chunk).decode())

        if source.is_file():
            # Single file upload
            await send_chunk("file", path=source.name, size=source.stat().st_size)
            stream_file_chunks(source)
            await send_chunk("end_of_file")
            await send_chunk("end_of_upload")
        else:
            # Directory upload
            await send_chunk("directory", path=source.name)

            for item in source.rglob("*") if recursive else source.iterdir():
                relative_path = str(item.relative_to(source))

                if item.is_dir():
                    if ignore_empty_dirs and not any(item.iterdir()):
                        continue
                    await send_chunk("directory_entry", path=relative_path)
                elif item.is_file():
                    await send_chunk(
                        "file_in_directory",
                        path=relative_path,
                        size=item.stat().st_size,
                    )
                    stream_file_chunks(item)
                    await send_chunk("end_of_file")

                if not recursive and item.is_dir():
                    continue

            await send_chunk("end_of_directory")

        # Wait for final confirmation from agent
        return await self.recv_from_agent()
