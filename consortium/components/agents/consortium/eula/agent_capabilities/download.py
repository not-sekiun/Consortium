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

    async def on_execute(self) -> Success | Failure | None:
        header = await self.recv_from_agent()
        if not header.success:
            return Failure(task_output_message=header)

        is_dir = header.data["type"] == "directory"
        target_name = pathlib.Path(header.data["path"]).name
        self.event_logger.update_progress(
            message=f"Starting download of {header.data['type']} '{target_name}'",
            percent_complete=0,
        )
        # For a single file the header is also the file announcement.
        current_file = None if is_dir else pathlib.Path(header.data["path"])
        current_file_size = 0 if is_dir else header.data.get("size", 0)
        downloaded_bytes = 0

        while True:
            response = await self.recv_from_agent()
            if not response.success:
                return Failure(task_output_message=response)

            match response.data.get("type"):
                case "file":
                    current_file = pathlib.Path(response.data["path"])
                    current_file_size = response.data.get("size", 0)
                    downloaded_bytes = 0
                    self.event_logger.update_progress(
                        message=f"Starting download of file '{current_file}'",
                        percent_complete=0,
                    )
                case "chunk":
                    try:
                        chunk = zlib.decompress(response.payload.data)
                    except zlib.error as exc:
                        return Failure(
                            message=f"Failed to decompress file chunk: {exc}"
                        )
                    downloaded_bytes += len(chunk)
                    self.event_logger.update_progress(
                        message=(
                            f"Downloading {current_file}: "
                            f"{downloaded_bytes}/{current_file_size} bytes"
                        ),
                        percent_complete=round(
                            downloaded_bytes / current_file_size * 100, 2
                        )
                        if current_file_size
                        else 0,
                    )
                case "directory":
                    self.event_logger.update_progress(
                        message=f"Created new directory '{response.data['path']}'",
                        percent_complete=100,
                    )
                case "end_of_file":
                    self.event_logger.artifact(
                        message=f"Downloaded file '{current_file}'"
                    )
                case "end_of_transfer":
                    if is_dir:
                        self.event_logger.artifact(
                            message=f"Downloaded directory '{target_name}'"
                        )
                    return Success(message="Download complete")
                case unknown:
                    return Failure(
                        message=(
                            f"Unknown message type received during download: {unknown}"
                        )
                    )
