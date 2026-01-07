import uuid
from collections.abc import AsyncIterable
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, JsonValue


class Payload:
    """
    Represents a binary payload that can be either a complete byte sequence or an
    asynchronous stream of byte chunks.

    Attributes:
        is_stream (bool): Indicates whether the payload is an asynchronous stream.

    """

    def __init__(self, payload: AsyncIterable[bytes] | bytes | bytearray):
        if isinstance(payload, bytes):
            self._payload = payload
            self.is_stream = False
        elif isinstance(payload, bytearray):
            self._payload = bytes(payload)
            self.is_stream = False
        elif isinstance(payload, AsyncIterable):
            self._payload = aiter(payload)
            self.is_stream = True
        else:
            raise TypeError(f"Unsupported payload type: {type(payload)}")

    @property
    def data(self) -> bytes:
        """
        Returns the entire payload as bytes if it is not an asynchronous streamn.
        Raises an error if the payload is an asynchronous stream.
        """
        if self.is_stream:
            raise ValueError("Payload is a stream. cannot retrieve bytes directly.")
        return self._payload

    async def load(self) -> bytes:
        """
        Asynchronously loads the entire payload stream into memory and returns it as
        bytes. If the payload is not a stream, returns the bytes directly.
        """
        if self.is_stream:
            chunks = bytearray()
            async for chunk in self._payload:
                chunks.extend(chunk)
            return bytes(chunks)
        else:
            return self._payload

    async def __aiter__(self):
        if self.is_stream:
            async for chunk in self._payload:
                yield chunk
        else:
            yield self._payload

    async def __anext__(self):
        if isinstance(self._payload, AsyncIterable):
            return await anext(self._payload)
        else:
            raise StopAsyncIteration


def _wrap_payload(v):
    if isinstance(v, Payload) or v is None:
        return v
    elif isinstance(v, (AsyncIterable, bytes, bytearray)):
        return Payload(v)
    else:
        raise TypeError(
            "payload must be of type `Payload`, `bytes`, `bytearray`, or "
            f"`AsyncIterable[bytes]`, but got `{type(v)}`"
        )


class AgentTaskMessageModel(BaseModel):
    """
    Model representing a task message sent to an agent.

    Attributes:
        task_id (uuid.UUID): Unique identifier for the task.
        command (str): The command to be executed by the agent.
        arguments (dict[str, JsonValue]): Arguments required for the command, must be
            JSON-serializable.
        data (dict[str, JsonValue]): Additional data related to the task, must be
            JSON-serializable.
        payload (Payload | None): Optional binary payload
            associated with the task.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: uuid.UUID
    command: str
    arguments: dict[str, JsonValue] = {}
    data: dict[str, JsonValue] = {}
    payload: Annotated[Payload | None, BeforeValidator(_wrap_payload)] = None

    def to_json(self):
        """
        Serialize the `AgentTaskMessageModel` to a JSON-compatible dictionary.
        """
        return {
            "task_id": str(self.task_id),
            "command": self.command,
            "arguments": self.arguments,
            "data": self.data,
        }


class AgentResultMessageModel(BaseModel):
    """
    Model representing a result message sent from an agent.

    Attributes:
        task_id (uuid.UUID): Unique identifier for the associated task.
        success (bool): Indicates if the task was successful.
        message (str): A message providing additional information about the result.
        data (dict[str, JsonValue]): Additional data related to the result, must be
            JSON-serializable.
        payload (Payload | None): Optional binary payload
            associated with the task.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: uuid.UUID
    success: bool
    message: str = ""
    data: dict[str, JsonValue] = {}
    payload: Annotated[Payload | None, BeforeValidator(_wrap_payload)] = None

    def to_json(self):
        """
        Serialize the `AgentResultMessageModel` to a JSON-compatible dictionary.
        """
        return {
            "task_id": str(self.task_id),
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }
