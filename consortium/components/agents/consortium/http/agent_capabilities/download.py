import pathlib
import zlib

from consortium.framework.agents import (
    BaseAgentCapability,
    Failure,
    Success,
    TaskLaunchMessageModel,
)
from consortium.framework.options import SingleValueOption


class DownloadCapability(BaseAgentCapability):
    name = "download"
    description = "Download a file or directory from the agent"
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
    mitre_attack_techniques = {"T1041", "T1005", "T1560.002"}

    async def on_launch(
        self, task_message: TaskLaunchMessageModel
    ) -> TaskLaunchMessageModel:
        # Remove `destination` before sending — it is a server-side concern only
        task_message.arguments.pop("destination", None)
        return task_message

    # TODO: Make download actually write artifacts via artifacts service and
    #  emit_artifact should properly log this event with reference to the artifact
    #  created
    async def on_execute(self) -> Success | Failure | None:
        header = await self.recv_from_agent()
        if not header.success:
            return Failure(task_output_message=header)

        is_dir = header.data["type"] == "directory"
        target_name = pathlib.Path(header.data["path"]).name
        # `header.data['type']` can be 'file' or 'directory' here for the initial header
        self.update_progress(
            message=f"Starting download of {header.data['type']} '{target_name}'",
            percent_complete=0,
        )

        # State for the current file being processed
        current_file = pathlib.Path(header.data["path"]) if not is_dir else None
        current_file_size = header.data["size"] if not is_dir else 0
        downloaded_bytes = 0

        response = header
        while True:
            if not response.success:  # Error response from agent, abort download
                return Failure(task_output_message=response)

            msg_type = response.data.get("type")

            # New file download starting within a directory
            if msg_type == "file":
                current_file = pathlib.Path(response.data["path"])
                current_file_size = response.data.get("size", 0)
                downloaded_bytes = 0
                # Ephemerally update the status of the task with the start of a new
                # file/directory download
                self.update_progress(
                    message=f"Starting download of file '{response.data['path']}'",
                    percent_complete=0,
                )
            elif msg_type == "chunk":
                try:
                    chunk = zlib.decompress(response.payload.data)
                except zlib.error as exc:
                    return Failure(
                        message=f"Failed to decompress file chunk: {exc}",
                    )
                downloaded_bytes += len(chunk)
                # Ephemeral update (Overwrites previous status but does not log to
                # task events to avoid flooding it)
                percent_complete = (
                    round(downloaded_bytes / current_file_size * 100, 2)
                    if current_file_size
                    else 0
                )
                self.update_progress(
                    message=f"Downloading {current_file}: {downloaded_bytes}/{current_file_size} bytes",
                    percent_complete=percent_complete,
                )
            elif msg_type == "directory":
                # Ephemerally update the status of the task with the start of a new
                # file/directory download
                self.update_progress(
                    message=f"Created new directory '{response.data['path']}'",
                    percent_complete=100,
                )
            elif msg_type == "end_of_file":
                self.emit_artifact(
                    message=f"Downloaded file '{current_file}'",
                )  # Log completion of file download in task events for task
                current_file = None
                current_file_size = 0
                downloaded_bytes = 0
            elif msg_type == "end_of_transfer":
                # Entire file or directory download is finished, emit to task events of
                # task and break loop if a directory was being downloaded, avoid logging
                # since we already log file download completion on 'end_of_file'
                if is_dir:
                    self.emit_artifact(
                        message=f"Downloaded directory '{target_name}'",
                    )
                break
            else:
                return Failure(
                    message=(
                        f"Unknown message type received during download: {msg_type}"
                    )
                )

            response = await self.recv_from_agent()

        # Return response to indicate successful download
        return Success(
            message=f"Downloaded {'directory' if is_dir else 'file'} '{target_name}'",
        )
