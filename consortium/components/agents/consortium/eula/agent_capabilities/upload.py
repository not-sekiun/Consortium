import os
import pathlib
import zlib

from consortium.framework.agents import (
    BaseAgentCapability,
    Failure,
    Success,
    TaskLaunchMessageModel,
)
from consortium.framework.options import SingleValueOption
from consortium.framework.signal_exceptions.agent_capabilties_signal_exception import (
    AgentCapabilityExecutionError,
    AgentCapabilityLaunchError,
)
from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    ResourceNotFoundError,
)


class UploadCapability(BaseAgentCapability):
    name = "upload"
    description = "Upload a file or directory to the agent"
    authors = {"Sekiun (github.com/not-sekiun)"}
    options = {
        SingleValueOption(
            name="source_asset",
            description="The asset ID of the source file or directory to upload.",
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

    async def on_launch(
        self, task_launch_message: TaskLaunchMessageModel
    ) -> TaskLaunchMessageModel:
        source_asset_id = task_launch_message.arguments["source_asset"]

        try:
            self.agent_file_manager_service.get_asset_by_asset_id(
                asset_id=source_asset_id
            )
        except ResourceNotFoundError:
            raise AgentCapabilityLaunchError(
                message=(
                    f"Asset with ID '{source_asset_id}' not found. Hint: Check that "
                    f"the `source_asset` ID is correct and that an asset with that ID "
                    f"exists on the server."
                )
            ) from None

        # Strip server-side-only arguments before sending to agent
        task_launch_message.arguments = {
            "destination": task_launch_message.arguments["destination"],
            "expand": task_launch_message.arguments["expand"],
            "overwrite": task_launch_message.arguments["overwrite"],
        }
        return task_launch_message

    async def on_execute(self) -> Success | Failure | None:
        source_asset_id = self.task_launch_message.arguments["source_asset"]
        recursive = self.task_launch_message.arguments["recursive"]
        chunk_size = self.task_launch_message.arguments["chunk_size"]
        compression_level = self.task_launch_message.arguments["compression_level"]

        try:
            asset = self.agent_file_manager_service.get_asset_by_asset_id(
                asset_id=source_asset_id
            )
        except ResourceNotFoundError:
            raise AgentCapabilityExecutionError(
                message=(
                    f"Asset with ID '{source_asset_id}' not found. Hint: The "
                    f"pre-capability execution validation passed so the asset may have "
                    f"been deleted between tasking and execution."
                )
            ) from None

        is_dir = asset.is_directory
        target_name = asset.name

        self.event_logger.update_progress(
            message=f"Starting upload of {'directory' if is_dir else 'file'} '{target_name}'",
            percent_complete=0,
        )

        # Get agent response to task launch message
        task_output_message = await self.recv_from_agent()
        if not task_output_message.success:
            return task_output_message.to_outcome()

        # Send the initial header announcement
        await self.send_to_agent(
            data={
                "type": "directory" if is_dir else "file",
                "path": target_name,
                **({"size": asset.size} if not is_dir else {}),
            },
        )

        async def send_file(file_path: pathlib.Path, relative_path: str = None):
            display_path = relative_path if relative_path else file_path.name
            file_size = file_path.stat().st_size

            # Announce the specific file
            await self.send_to_agent(
                data={
                    "type": "file",
                    "path": display_path,
                    "size": file_size,
                },
            )

            try:
                with open(file_path, mode="rb") as file:
                    uploaded_bytes = 0
                    while True:
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break

                        uploaded_bytes += len(chunk)
                        chunk = zlib.compress(chunk, level=compression_level)

                        # Send chunk payload
                        await self.send_to_agent(
                            data={"type": "chunk"},
                            payload=chunk,
                        )

                        self.event_logger.update_progress(
                            message=f"Uploading {display_path}: {uploaded_bytes}/{file_size} bytes",
                            percent_complete=round(uploaded_bytes / file_size * 100, 2)
                            if file_size
                            else 0,
                        )
                # Signal file completion
                await self.send_to_agent(data={"type": "end_of_file"})
                return True
            except PermissionError as exc:
                self.event_logger.error(
                    message=f"Failed to upload asset '{target_name}': {exc}"
                )
                return False

        async def send_directory(directory_path: pathlib.Path):
            base_parent = directory_path.parent
            for root, dirs, files in os.walk(directory_path):
                root_path = pathlib.Path(root)
                for directory in dirs:
                    dir_path = root_path / directory
                    # Announce new directory
                    await self.send_to_agent(
                        data={
                            "type": "directory",
                            "path": str(dir_path.relative_to(base_parent)),
                        },
                    )
                for file in files:
                    file_path = root_path / file
                    relative_path = str(file_path.relative_to(base_parent))
                    if not await send_file(file_path, relative_path):
                        return False

                if not recursive:
                    break
            return True

        # Process File / Directory
        if is_dir:
            success = await send_directory(asset.path)
        else:
            success = await send_file(asset.path)

        # Finalize
        if success:
            await self.send_to_agent(data={"type": "end_of_transfer"})
            self.event_logger.artifact(
                message=f"Uploaded {'directory' if is_dir else 'file'} '{target_name}'"
            )
            return Success(message="Upload complete")
        else:
            return Failure(message="Upload failed during transfer")
