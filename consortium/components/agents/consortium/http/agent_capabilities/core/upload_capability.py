import base64
from collections.abc import AsyncGenerator
from copy import deepcopy
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO

from consortium.framework.agents.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
    SupportedOS,
)
from consortium.framework.exceptions.agent_capabilties_framework_exception import (
    AgentCapabilityTaskingError,
)
from consortium.framework.options import SingleValueOption


class _UploadAgentCapabilityMessageType(StrEnum):
    HEADER = "HEADER"
    FILE_CHUNK = "FILE_CHUNK"
    END_OF_FILE = "END_OF_FILE"


def _file_chunking_generator(file: BinaryIO, chunk_size: int):
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        yield chunk


def _process_file(agent_message: AgentTaskMessageModel):
    with open(file=str(agent_message.arguments["source"]), mode="rb") as file:
        header_message = deepcopy(agent_message)
        header_message.data["message_type"] = str(
            _UploadAgentCapabilityMessageType.HEADER,
        )
        if agent_message.arguments["destination"]:
            header_message.data["filepath"] = agent_message.arguments["destination"]
        else:
            header_message.data["filepath"] = str(
                Path(agent_message.arguments["source"]).absolute().name,
            )
        yield header_message

        for chunk in _file_chunking_generator(
            file=file,
            chunk_size=agent_message.arguments["chunk_size"],
        ):
            chunk_message = deepcopy(agent_message)
            chunk_message.data["message_type"] = str(
                _UploadAgentCapabilityMessageType.FILE_CHUNK,
            )
            chunk_message.data["file_chunk"] = base64.b64encode(chunk)
            yield chunk_message

        eof_message = deepcopy(agent_message)
        eof_message.data["message_type"] = str(
            _UploadAgentCapabilityMessageType.END_OF_FILE,
        )
        yield eof_message


def _process_directory(
    agent_message: AgentTaskMessageModel,
):
    if agent_message["data"]["recursive"]:
        filepath_iterator = Path(agent_message["data"]["source"]).rglob("*")
    else:
        filepath_iterator = Path(agent_message["data"]["source"]).iterdir()

    for filepath in filepath_iterator:
        with open(file=str(filepath), mode="rb") as file:
            header_message = deepcopy(agent_message)
            header_message.data["message_type"] = str(
                _UploadAgentCapabilityMessageType.HEADER,
            )
            relative_filepath = filepath.absolute().relative_to(
                Path(agent_message.data["source"]),
            )
            if agent_message.data["destination"]:
                header_message.data["filepath"] = str(
                    Path(agent_message["data"]["destination"]) / relative_filepath,
                )
            else:
                header_message.data["filepath"] = str(
                    relative_filepath.parents[0].relative_to(filepath),
                )
            yield header_message

            for chunk in _file_chunking_generator(
                file=file,
                chunk_size=agent_message.data["chunk_size"],
            ):
                chunk_message = deepcopy(agent_message)
                chunk_message.data["message_type"] = str(
                    _UploadAgentCapabilityMessageType.FILE_CHUNK,
                )
                chunk_message.data["file_chunk"] = base64.b64encode(chunk)
                yield chunk_message

            eof_message = deepcopy(agent_message)
            eof_message.data["message_type"] = str(
                _UploadAgentCapabilityMessageType.END_OF_FILE,
            )
            yield eof_message


class UploadCapability(BaseAgentCapability):
    name = "upload"
    description = (
        "Upload a file or directory, either recursively or non-recursively, to the "
        "agent."
    )
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    options = {
        SingleValueOption(
            name="source",
            description=(
                "The filepath of the file or directory to upload to the agent."
            ),
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="destination",
            description=(
                "The full filepath to write the uploaded file or directory to on the "
                "agent. If not provided, the file or directory will be saved in the "
                "current working directory."
            ),
            required=False,
            value_type=str,
        ),
        SingleValueOption(
            name="recursive",
            description=(
                "Whether to upload the source directory and its contents recursively. "
                "If uploading is not recursive, only the files within the directory "
                "will be uploaded. This option cannot be set to true if the source is "
                "a file."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="chunk_size",
            description=(
                "Size of the chunks to use in bytes when uploading files to the agent."
            ),
            required=False,
            value_type=int,
            default_value=1024,
        ),
    }
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def handle_sending_agent_task_messages(
        self,
        agent_message: AgentTaskMessageModel,
    ) -> AsyncGenerator[AgentTaskMessageModel]:
        path = Path(agent_message.arguments["source"])

        if not path.exists():
            raise AgentCapabilityTaskingError(
                message=(
                    f"Failed to upload file or directory {agent_message.arguments['source']}. "
                    "The source file or directory does not exist."
                ),
            )
        if not path.is_file() and agent_message.arguments["recursive"]:
            raise AgentCapabilityTaskingError(
                message=(
                    f"Failed to upload file or directory {agent_message.arguments['source']}. "
                    "Recursive uploading is only supported for files."
                ),
            )

        if path.is_file():
            for message in _process_file(
                agent_message=agent_message,
            ):
                yield message
        else:
            for message in _process_directory(
                agent_message=agent_message,
            ):
                yield message

    async def handle_receiving_agent_response_messages(
        self,
        agent_response: AgentResultMessageModel,
    ) -> AsyncGenerator[AgentResultMessageModel]:
        yield agent_response
