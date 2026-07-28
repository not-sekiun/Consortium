from collections.abc import AsyncIterable
from typing import Annotated

from pydantic import UUID4, BaseModel, BeforeValidator, ConfigDict, JsonValue

from consortium.framework.agents.agent_outcomes import Failure, Success


class Payload:
    """Binary payload that wraps either a complete byte sequence or an async stream of byte chunks.

    Provides a unified interface for both in-memory bytes and streaming data so that
    callers do not need to branch on the data source type.

    Attributes:
        is_stream: True if the payload is backed by an async iterable rather than an
            in-memory byte sequence.
    """

    def __init__(self, payload: AsyncIterable[bytes] | bytes | bytearray):
        """Initialize the payload from a byte sequence or async iterable.

        Args:
            payload: The source data. Accepts a complete in-memory byte sequence
                (bytes or bytearray) or an async iterable of byte chunks for streaming.

        Raises:
            TypeError: If payload is not bytes, bytearray, or AsyncIterable[bytes].
        """
        self.is_stream: bool
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
        """The complete payload as bytes for non-streaming payloads.

        Raises:
            ValueError: If the payload is backed by an async stream; use load() instead.

        Returns:
            The in-memory payload bytes.
        """
        if self.is_stream:
            raise ValueError("Payload is a stream. cannot retrieve bytes directly.")
        return self._payload

    async def load(self) -> bytes:
        """Load the entire payload into memory and return it as a byte sequence.

        Buffers the full stream into a single byte sequence for streaming payloads,
        or returns the in-memory bytes directly for non-streaming payloads.

        Returns:
            The complete payload as a contiguous byte sequence.
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


class TaskLaunchMessageModel(BaseModel):
    """Message sent to an agent to initiate a new task execution.

    Carries the task identity, the command name, and any structured arguments and
    data the capability needs. An optional binary payload can accompany the message
    for capabilities that require file or binary input.

    Attributes:
        task_id: Unique identifier for the task being launched.
        command: The name of the capability command the agent should execute.
        arguments: Command arguments required to execute the capability. Must be
            JSON-serializable.
        data: Supplementary data associated with the task. Must be JSON-serializable.
        payload: Optional binary payload accompanying the task, such as a file to be
            processed by the agent.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: UUID4
    command: str
    arguments: dict[str, JsonValue] = {}
    data: dict[str, JsonValue] = {}
    payload: Annotated[Payload | None, BeforeValidator(_wrap_payload)] = None

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the message to a JSON-compatible dictionary, excluding the binary payload.

        Returns:
            A dictionary containing task_id, command, arguments, and data. The payload
                field is omitted since binary data is not JSON-serializable.
        """
        return {
            "task_id": str(self.task_id),
            "command": self.command,
            "arguments": self.arguments,
            "data": self.data,
        }


class TaskInputMessageModel(BaseModel):
    """Message sent to an agent to provide additional input to a running task.

    Used when a task requires interactive or incremental input after the initial
    launch message has been sent.

    Attributes:
        task_id: Unique identifier of the task receiving the input.
        data: Structured input data for the running task. Must be JSON-serializable.
        payload: Optional binary payload accompanying the input, such as a file chunk
            or continuation data.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: UUID4
    data: dict[str, JsonValue] = {}
    payload: Annotated[Payload | None, BeforeValidator(_wrap_payload)] = None

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the message to a JSON-compatible dictionary, excluding the binary payload.

        Returns:
            A dictionary containing the task_id and data. The payload field is omitted
                since binary data is not JSON-serializable.
        """
        return {
            "task_id": str(self.task_id),
            "data": self.data,
        }


class TaskOutputMessageModel(BaseModel):
    """Message sent from an agent reporting the result of a completed task.

    Carries whether the task succeeded, a human-readable result summary, and any
    structured output data or binary artifacts produced during execution.

    Attributes:
        task_id: Unique identifier of the task that produced this output.
        success: True if the task completed successfully, False on failure.
        message: Human-readable summary of the task result or error description.
        data: Structured output data from the task. Must be JSON-serializable.
        payload: Optional binary artifact produced by the task, such as a captured
            file or command output blob.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: UUID4
    success: bool
    message: str = ""
    data: dict[str, JsonValue] = {}
    payload: Annotated[Payload | None, BeforeValidator(_wrap_payload)] = None

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the message to a JSON-compatible dictionary, excluding the binary payload.

        Returns:
            A dictionary containing task_id, success, message, and data. The payload
                field is omitted since binary data is not JSON-serializable.
        """
        return {
            "task_id": str(self.task_id),
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }

    def to_outcome(self) -> Success | Failure:
        """Convert the message into a Success or Failure outcome object.

        Returns:
            A Success instance if success is True, otherwise a Failure instance.
        """

        if self.success:
            return Success(task_output_message=self)
        else:
            return Failure(task_output_message=self)
