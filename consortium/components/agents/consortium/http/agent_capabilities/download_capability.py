import base64
import pathlib

from consortium.framework.agents.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
)
from consortium.framework.options import SingleValueOption

# def _validate_chunk_size_argument(chunk_size: int):
#     """
#     Check that the chunk size to use when downloading files from the agent is greater
#     than 0.
#     """
#     if chunk_size <= 0 or chunk_size > 26214400:
#         raise OptionValueValidationError(
#             f"The provided chunk size, '{chunk_size}', must be an integer greater than "
#             "0 but less than 26214400 (25MB).",
#         )


# def _validate_compression_level_argument(compression_level: int):
#     """
#     Check that the compression level to use when compressing the chunked downloads is
#     between 0 and 9.
#     """
#     if compression_level < 0 or compression_level > 9:
#         raise OptionValueValidationError(
#             f"The provided compression level, '{compression_level}', must be an integer "
#             "between 0 and 9.",
#         )


class DownloadCapability(BaseAgentCapability):
    name = "download"
    description = "Download a file from the agent."
    authors = {"Sekiun (github.com/not-sekiun)"}
    is_atomic = True
    options = {
        SingleValueOption(
            name="source",
            description=(
                "The full or relative filepath of the file or directory to download "
                "from the agent."
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
                "the directory will be downloaded. This option will be ignored if the "
                "source is a file."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="chunk_size",
            description=(
                "Size of the uncompressed chunks to use in bytes when downloading files "
                "from the agent. By default, the chunk size is 1MB. Larger values may "
                "improve download speed at the cost of increasing memory usage."
            ),
            required=False,
            value_type=int,
            default_value=1000000,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=26214400,
            # validating_function=_validate_chunk_size_argument,
        ),
        SingleValueOption(
            name="ignore_empty_dirs",
            description=(
                "Ignore empty directories when downloading from the agent. Note that "
                "when downloading a directory non-recursively, empty directories will "
                "still be created in place of non-empty nested directories to signify "
                "their existence."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="compression_level",
            description=(
                "The zlib (gzip backend) compression level to use when compressing the "
                "chunked downloads. The level of compression is represented by an "
                "integer ranging from 0 (no compression) to 9 (maximum compression). "
                "Larger values may improve download speed at the cost of increasing "
                "resource usage."
            ),
            required=False,
            value_type=int,
            default_value=5,
            greater_than_or_equal_to=0,
            less_than_or_equal_to=9,
            # validating_function=_validate_compression_level_argument,
        ),
        SingleValueOption(
            name="expand",
            description=(
                "Attempt to expand environment variables when provided while attempting "
                "to resolve the source directory. By default, this is disabled."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
    }

    async def execute(
        self,
        task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel:
        task_message.arguments.pop("destination")

        header_result_message = await self.send_and_recv_from_agent(
            task_message=task_message,
        )
        resolved_source_path = header_result_message.data["resolved_source_path"]
        is_directory = header_result_message.data["is_directory"]

        if not is_directory:
            filename = pathlib.Path(
                header_result_message.data["resolved_source_path"],
            ).name
            print(f"Downloading {filename}")
            while True:
                result = await self.recv_from_agent()
                if result.data["response_type"] == "end_of_file":
                    break
                print(f"    Got chunk of data with length {result.data['file_chunk']}")
            print(f"Downloaded {filename}")
        else:
            directory_path = pathlib.Path(
                header_result_message.data["resolved_source_path"],
            ).name
            print(f"Downloading {directory_path}")
            while True:
                result = await self.recv_from_agent()
                if result.data["response_type"] == "directory":
                    directory_path = result.data["directory_path"]
                    print(f"    Created directory {directory_path}")
                elif result.data["response_type"] == "start_of_directory_file":
                    relative_file_path = result.data["relative_file_path"]
                    print(f"    Downloading {relative_file_path}")
                    while True:
                        result = await self.recv_from_agent()
                        if result.data["response_type"] != "file_chunk":
                            break
                        file_chunk = base64.b64decode(result.data["file_chunk"])
                        print(
                            f"        Got chunk of data with length {len(file_chunk)}",
                        )
                    print(f"    Downloaded {relative_file_path}")
                elif result.data["response_type"] == "end_of_directory":
                    print(f"Downloaded {directory_path}")
                    break

        download_type = "directory" if is_directory else "file"
        result = AgentResultMessageModel(
            task_id=task_message.task_id,
            success=True,
            message=(
                f"Finished downloading {download_type} '{resolved_source_path}' from "
                "agent."
            ),
            data={},
        )

        return result
