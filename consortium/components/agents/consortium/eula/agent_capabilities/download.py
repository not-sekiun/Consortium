import pathlib
import tempfile
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
            description="Chunk size in bytes. Larger values improve speed but use more memory. Chunk size is limited to 8MiB",
            required=False,
            value_type=int,
            default_value=1024 * 1024,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=8 * 1024 * 1024,
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
        # Remove `destination` before sending — it is a server-side concern only
        task_launch_message.arguments.pop("destination", None)
        return task_launch_message

    async def on_execute(self) -> Success | Failure | None:
        header = await self.recv_from_agent()
        if not header.success:
            return Failure(task_output_message=header)

        with tempfile.TemporaryDirectory() as temp_dir:
            # For a single file the header is also the file announcement.
            is_dir = header.data["type"] == "directory"
            full_path = header.data["path"]
            path_basename = pathlib.Path(full_path).name
            current_file = None if is_dir else pathlib.Path(temp_dir) / path_basename
            current_file_size = 0 if is_dir else header.data.get("size", 0)
            downloaded_bytes = 0

            if is_dir:
                (pathlib.Path(temp_dir) / path_basename).mkdir(
                    parents=True, exist_ok=True
                )
            else:
                (pathlib.Path(temp_dir) / path_basename).touch()

            self.event_logger.update_progress(
                message=f"Starting download of {header.data['type']} '{header.data['path']}'",
                percent_complete=0,
            )

            while True:
                response = await self.recv_from_agent()
                if not response.success:
                    return Failure(task_output_message=response)

                match response.data.get("type"):
                    case "file":
                        current_file = (
                            pathlib.Path(temp_dir)
                            / path_basename
                            / response.data["path"]
                        )
                        current_file_size = response.data.get("size", 0)
                        downloaded_bytes = 0
                        self.event_logger.update_progress(
                            message=f"Starting download of file '{response.data['path']}'",
                            percent_complete=0,
                        )
                        current_file.touch()
                    case "chunk":
                        try:
                            chunk = zlib.decompress(await response.payload.read())
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
                        with current_file.open("ab") as file:
                            file.write(chunk)
                    case "directory":
                        self.event_logger.update_progress(
                            message=f"Created new directory '{response.data['path']}'",
                            percent_complete=100,
                        )
                        (
                            pathlib.Path(temp_dir)
                            / path_basename
                            / response.data["path"]
                        ).mkdir(parents=True, exist_ok=True)
                    case "end_of_file":
                        self.event_logger.artifact(
                            message=f"Downloaded file '{current_file.relative_to(temp_dir)}'"
                        )
                    case "end_of_transfer":
                        if is_dir:
                            self.event_logger.artifact(
                                message=f"Downloaded directory '{full_path}'"
                            )
                            await (
                                self.agent_file_manager_service.add_artifact_directory(
                                    path=pathlib.Path(temp_dir) / path_basename,
                                    name=path_basename,
                                )
                            )
                        else:
                            await self.agent_file_manager_service.add_artifact_file(
                                path=pathlib.Path(temp_dir) / path_basename,
                                name=path_basename,
                            )
                        return Success(message="Download complete")
                    case unknown:
                        return Failure(
                            message=(
                                f"Unknown message type received during download: {unknown}"
                            )
                        )
