import pathlib
import zlib

from consortium.framework.agents import (
    Failure,
    IncomingStreamCapability,
    Success,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.options import SingleValueOption


class DownloadCapability(IncomingStreamCapability):
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
        self, task_launch_message: TaskLaunchMessageModel
    ) -> TaskLaunchMessageModel:
        # Remove `destination` before sending, it is a server-side concern only
        task_launch_message.arguments.pop("destination", None)
        return task_launch_message

    # TODO: Make download actually write artifacts via artifacts service and
    #  emit_artifact should properly log this event with reference to the artifact
    #  created
    async def on_handle_incoming_message(
        self, task_output_message: TaskOutputMessageModel
    ) -> Success | Failure | None:
        response = task_output_message
        # Per-transfer state that persists across the streamed messages. Held on
        # `self.environment` since each message arrives in a separate hook call rather
        # than as iterations of a single local loop.
        env = self.environment

        # An error response from the agent aborts the download at any point.
        if not response.success:
            return Failure(task_output_message=response)

        # The first message is the transfer header. Capture the top-level transfer
        # metadata once so `end_of_transfer` can report against it. `header.data['type']`
        # can be 'file' or 'directory' here for the initial header.
        if not hasattr(env, "is_dir"):
            env.is_dir = response.data["type"] == "directory"
            env.target_name = pathlib.Path(response.data["path"]).name
            env.current_file = None
            env.current_file_size = 0
            env.downloaded_bytes = 0
            self.update_progress(
                message=(
                    f"Starting download of {response.data['type']} '{env.target_name}'"
                ),
                percent_complete=0,
            )

        msg_type = response.data.get("type")

        # New file download starting within a directory (or the single-file header)
        if msg_type == "file":
            env.current_file = pathlib.Path(response.data["path"])
            env.current_file_size = response.data.get("size", 0)
            env.downloaded_bytes = 0
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
            env.downloaded_bytes += len(chunk)
            # Ephemeral update (Overwrites previous status but does not log to
            # task events to avoid flooding it)
            percent_complete = (
                round(env.downloaded_bytes / env.current_file_size * 100, 2)
                if env.current_file_size
                else 0
            )
            self.update_progress(
                message=f"Downloading {env.current_file}: {env.downloaded_bytes}/{env.current_file_size} bytes",
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
                message=f"Downloaded file '{env.current_file}'",
            )  # Log completion of file download in task events for task
            env.current_file = None
            env.current_file_size = 0
            env.downloaded_bytes = 0
        elif msg_type == "end_of_transfer":
            # Entire file or directory download is finished, emit to task events of
            # task and finish the stream if a directory was being downloaded, avoid
            # logging since we already log file download completion on 'end_of_file'
            if env.is_dir:
                self.emit_artifact(
                    message=f"Downloaded directory '{env.target_name}'",
                )
            return Success(
                message=(
                    f"Downloaded {'directory' if env.is_dir else 'file'} "
                    f"'{env.target_name}'"
                ),
            )
        else:
            return Failure(
                message=(f"Unknown message type received during download: {msg_type}")
            )

        # No terminal signal for this message: keep receiving the next one.
        return None
