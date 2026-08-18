import asyncio
import os
import tempfile
import weakref
from collections.abc import AsyncIterable, AsyncIterator, Mapping
from pathlib import Path
from typing import IO, Annotated, Self

from pydantic import (
    UUID4,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    model_validator,
)

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    PayloadTooLargeError,
)
from consortium.framework.agents._resource_limits import SPOOL_TO_DISK_ABOVE
from consortium.framework.agents.agent_outcomes import Failure, Success

# Read granularity for file-backed payloads and for consuming a receive source.
_DEFAULT_CHUNK_SIZE = 64 * 1024


class Payload:
    """A binary attachment on a task message.

    Read a payload whole or stream it a chunk at a time, either of them any number of
    times:

        data = await payload.read()
        async for chunk in payload: ...

    Construct one from bytes already in hand, from a file, from an open file object,
    or from an async byte source such as an upload:

        Payload.from_bytes(data)
        await Payload.from_file(path)
        await Payload.from_file_like(fileobj)
        await Payload.from_async_iterable(source)

    Every constructor takes a copy of its source, so a payload never refers back to it
    and is unaffected by what happens to it afterwards. A large payload is held on disk
    rather than in memory, and is cleaned up once nothing refers to the payload, so
    callers never manage its storage.

    Attributes:
        size: The size of the payload in bytes, known before it is read.
        filename: The originating filename, if known, or None.
        content_type: The MIME content type, if known, or None.
    """

    def __init__(
        self,
        *,
        data: bytes | None = None,
        spool: tempfile.SpooledTemporaryFile | None = None,
        size: int,
        resident_size: int | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        # Not part of the public surface: callers construct via one of the `from_*` classmethods.
        # Exactly one of `data` (bytes in memory) or `spool` (a SpooledTemporaryFile that
        # may or may not have rolled to disk) backs the payload; readers never distinguish.
        if (data is None) == (spool is None):
            raise ValueError("Payload must be backed by exactly one of data or spool.")
        self._data = data
        self._spool = spool
        # Bytes held in memory: all of a from_bytes payload, and a received one that
        # stayed under the spill threshold; zero once the spool has rolled to disk.
        #
        # Private despite being read from outside this class. It exists solely for the
        # task messages queue's memory accounting, and nothing on the read path depends
        # on it or on where a payload's bytes live: a capability that reaches for this is
        # asking a question the payload interface deliberately does not answer.
        self._resident_size = len(data) if data is not None else resident_size
        # Close the spool when this payload is collected. For a rolled spool that deletes
        # the temporary file; for one still in memory it frees the buffer. The finalizer
        # holds only the spool, never `self`, so it does not pin the payload alive.
        #
        # `SpooledTemporaryFile` unlinks the file at creation (POSIX) or opens it
        # delete-on-close (Windows), so a temporary file cannot outlive the process even
        # if it never gets collected: a hard crash leaves no orphan on disk.
        self._finalizer = (
            weakref.finalize(self, self._close_quietly, spool)
            if spool is not None
            else None
        )
        self.size = size
        self.filename = filename
        self.content_type = content_type

    @classmethod
    def from_bytes(
        cls,
        data: bytes | bytearray,
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> Payload:
        """Build an in-memory payload from a complete byte sequence.

        Args:
            data: The payload bytes. A bytearray is copied to immutable bytes.
            filename: Optional originating filename.
            content_type: Optional MIME content type.

        Returns:
            An in-memory payload holding the given bytes.
        """
        data = bytes(data)
        return cls(
            data=data,
            size=len(data),
            filename=filename,
            content_type=content_type,
        )

    @classmethod
    async def from_async_iterable(
        cls,
        source: AsyncIterable[bytes],
        *,
        max_size: int | None = None,
        spool_to_disk_above: int = SPOOL_TO_DISK_ABOVE,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> Payload:
        """Consume an async byte source into a payload.

        When a size cap is given it is enforced as bytes arrive, so an oversized source
        is rejected without being read to the end.

        Args:
            source: An async iterable of byte chunks, such as an upload being received.
            max_size: Optional hard maximum total size in bytes, raising
                `PayloadTooLargeError` when exceeded. Defaults to None, meaning no cap:
                the framework imposes no payload size of its own, so a transport that
                wants one passes its own here.
            spool_to_disk_above: Size in bytes above which the payload is held on disk
                instead of in memory. Defaults to the framework's configured threshold.
            filename: Optional originating filename.
            content_type: Optional MIME content type.

        Raises:
            PayloadTooLargeError: If the source yields more than `max_size` bytes.

        Returns:
            The received payload.
        """
        spool = tempfile.SpooledTemporaryFile(max_size=spool_to_disk_above)
        total = 0
        try:
            async for chunk in source:
                total += len(chunk)
                if max_size is not None and total > max_size:
                    raise PayloadTooLargeError(max_size=max_size)
                await asyncio.to_thread(spool.write, chunk)
        except BaseException:
            # Discard the spool on cap violation, cancellation, or a source error. Closing
            # a rolled spool deletes its temporary file; closing an in-memory one frees the
            # buffer.
            cls._close_quietly(spool)
            raise

        return cls._from_filled_spool(
            spool,
            total=total,
            spool_to_disk_above=spool_to_disk_above,
            filename=filename,
            content_type=content_type,
        )

    @classmethod
    async def from_file(
        cls,
        path: str | os.PathLike[str],
        *,
        max_size: int | None = None,
        spool_to_disk_above: int = SPOOL_TO_DISK_ABOVE,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> Payload:
        """Build a payload from a file on disk, copying its contents.

        The file is read once, now, into the payload's own storage. The payload is a
        snapshot of the file as it was at this moment and never refers to it again, so
        the original may be modified, moved or deleted immediately afterwards, and is
        not held open in the meantime.

        A file at or below `spool_to_disk_above` is held in memory, so a small file
        costs a read rather than a copy on disk.

        Args:
            path: The file to read.
            max_size: Optional hard maximum total size in bytes, raising
                `PayloadTooLargeError` when exceeded. Defaults to None, meaning no cap.
            spool_to_disk_above: Size in bytes above which the payload is held on disk
                instead of in memory. Defaults to the framework's configured threshold.
            filename: Originating filename recorded on the payload. Defaults to the name
                of `path`.
            content_type: Optional MIME content type.

        Raises:
            OSError: If the file cannot be opened or read.
            PayloadTooLargeError: If the file holds more than `max_size` bytes.

        Returns:
            The payload.
        """
        # Copied rather than referenced. A message can sit queued for days, so a path
        # read lazily is a file that may be deleted or rewritten before it is consumed,
        # and holding its descriptor open instead blocks deletion outright on Windows.
        path = Path(path)
        spool = tempfile.SpooledTemporaryFile(max_size=spool_to_disk_above)
        try:
            total = await asyncio.to_thread(
                cls._copy_path_into_spool, path, spool, max_size
            )
        except BaseException:
            cls._close_quietly(spool)
            raise

        return cls._from_filled_spool(
            spool,
            total=total,
            spool_to_disk_above=spool_to_disk_above,
            filename=path.name if filename is None else filename,
            content_type=content_type,
        )

    @classmethod
    async def from_file_like(
        cls,
        fileobj: IO[bytes],
        *,
        max_size: int | None = None,
        spool_to_disk_above: int = SPOOL_TO_DISK_ABOVE,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> Payload:
        """Build a payload from an open binary file object, copying its contents.

        Reads from the object's current position until it is exhausted and copies what
        it yields into the payload's own storage. The object is not rewound first, not
        closed afterwards, and not referred to again once this returns.

        Args:
            fileobj: A file object opened in binary mode, such as an open file or a
                `BytesIO`.
            max_size: Optional hard maximum total size in bytes, raising
                `PayloadTooLargeError` when exceeded. Defaults to None, meaning no cap.
            spool_to_disk_above: Size in bytes above which the payload is held on disk
                instead of in memory. Defaults to the framework's configured threshold.
            filename: Optional originating filename.
            content_type: Optional MIME content type.

        Raises:
            OSError: If the object cannot be read.
            PayloadTooLargeError: If the object yields more than `max_size` bytes.

        Returns:
            The payload.
        """
        spool = tempfile.SpooledTemporaryFile(max_size=spool_to_disk_above)
        try:
            total = await asyncio.to_thread(
                cls._copy_into_spool, fileobj, spool, max_size
            )
        except BaseException:
            cls._close_quietly(spool)
            raise

        return cls._from_filled_spool(
            spool,
            total=total,
            spool_to_disk_above=spool_to_disk_above,
            filename=filename,
            content_type=content_type,
        )

    async def read(self) -> bytes:
        """Read the whole payload and return it as a single byte sequence.

        This is the point at which a payload is fully materialized in memory, including a
        payload that spilled to disk and has been costing a queue nothing since. The bytes
        returned sit outside every queue's memory accounting, and a payload arrives as
        large as its transport allowed, so what is affordable here is the caller's own
        bound rather than one the framework imposes. Prefer `async for chunk in payload`
        unless the whole payload is genuinely needed at once.

        Returns:
            The complete payload as a contiguous byte sequence.
        """
        if self._data is not None:
            return self._data
        return await asyncio.to_thread(self._read_spool_fully)

    def __aiter__(self) -> AsyncIterator[bytes]:
        """Stream the payload as byte chunks: `async for chunk in payload`.

        A single reader consumes the payload from start to end, so do not iterate the
        same payload concurrently.
        """
        return self._stream()

    async def _stream(self) -> AsyncIterator[bytes]:
        if self._data is not None:
            yield self._data
            return

        # Rewind so each read starts from the beginning; the spool is re-readable.
        await asyncio.to_thread(self._spool.seek, 0)
        while True:
            chunk = await asyncio.to_thread(self._spool.read, _DEFAULT_CHUNK_SIZE)
            if not chunk:
                break
            yield chunk

    @classmethod
    def _from_filled_spool(
        cls,
        spool: tempfile.SpooledTemporaryFile,
        *,
        total: int,
        spool_to_disk_above: int,
        filename: str | None,
        content_type: str | None,
    ) -> Payload:
        # A SpooledTemporaryFile rolls to disk once its size exceeds max_size, so anything
        # over the threshold no longer sits in memory. Guard the degenerate threshold of 0,
        # which disables rollover and keeps the payload in memory.
        rolled = spool_to_disk_above > 0 and total > spool_to_disk_above
        return cls(
            spool=spool,
            size=total,
            resident_size=0 if rolled else total,
            filename=filename,
            content_type=content_type,
        )

    @staticmethod
    def _copy_path_into_spool(
        path: Path,
        spool: tempfile.SpooledTemporaryFile,
        max_size: int | None,
    ) -> int:
        with open(path, "rb") as fileobj:
            return Payload._copy_into_spool(fileobj, spool, max_size)

    @staticmethod
    def _copy_into_spool(
        fileobj: IO[bytes],
        spool: tempfile.SpooledTemporaryFile,
        max_size: int | None,
    ) -> int:
        # Blocking on purpose: the whole copy goes to one worker thread, where a file
        # read costs no more than the write beside it, rather than paying the event loop
        # a thread hop per chunk the way a streamed source has to.
        total = 0
        while chunk := fileobj.read(_DEFAULT_CHUNK_SIZE):
            total += len(chunk)
            if max_size is not None and total > max_size:
                raise PayloadTooLargeError(max_size=max_size)
            spool.write(chunk)
        return total

    def _read_spool_fully(self) -> bytes:
        self._spool.seek(0)
        return self._spool.read()

    @staticmethod
    def _close_quietly(fileobj) -> None:
        # Closing a rolled SpooledTemporaryFile deletes its backing temporary file;
        # closing an in-memory one frees its buffer. Either way this is the payload's
        # cleanup.
        try:
            fileobj.close()
        except OSError:
            pass


def _wrap_payload(value: object) -> Payload | None:
    # Lets a caller hand a message raw bytes wherever a payload is expected, which is
    # what a capability holding a small blob in memory wants.
    #
    # Raises ValueError rather than TypeError so pydantic reports it as an ordinary
    # validation failure instead of letting it escape the model. That is also what stops
    # an agent smuggling a payload through the JSON: nothing decoded from JSON is a
    # `Payload` or `bytes`, so a `payload` key fails here on its type alone and no
    # message needs a hand written guard against one.
    if isinstance(value, Payload) or value is None:
        return value
    if isinstance(value, (bytes, bytearray)):
        return Payload.from_bytes(value)
    raise ValueError(
        "payload must be of type `Payload`, `bytes`, or `bytearray`, but got "
        f"`{type(value)}`"
    )


class _Message(BaseModel):
    # Base of every agent message. Not a message itself: it declares no fields and is
    # never sent or received. It exists so that one place pins the model configuration
    # and the JSON conversion that every message shares, rather than each model carrying
    # its own copy of both.
    #
    # `extra="forbid"` guards the flat protocol fields, so a drifted or hostile envelope
    # is rejected rather than silently ignored. It does not reach into the open
    # `arguments` and `data` dictionaries, which are opaque maps the framework carries
    # but never opens, so capabilities extend those freely without a protocol change.
    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_json(
        cls,
        message_json: str | bytes | bytearray | Mapping[str, JsonValue],
    ) -> Self:
        """Validate JSON reported by an agent into this message.

        The counterpart to `to_json`, for a listener whose agents speak the framework's
        JSON. A listener with a wire format of its own parses that format and constructs
        the message directly instead.

        Args:
            message_json: The message as raw JSON text or bytes, or as an already
                decoded JSON object.

        Raises:
            ValueError: If the JSON cannot be decoded, is not an object, carries an
                unexpected key, or fails field validation.

        Returns:
            The validated message.
        """
        if isinstance(message_json, (str, bytes, bytearray)):
            return cls.model_validate_json(message_json)
        return cls.model_validate(message_json)

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the message to a JSON-compatible dictionary.

        Any binary payload is left out, and is sent alongside this rather than inside it.

        Returns:
            The message as a dictionary of JSON-compatible values.
        """
        return self.model_dump(mode="json")


class _TaskMessage(_Message):
    # Common core of every message addressed to a specific task: the task it belongs to,
    # and the binary that may travel with it. Not a message in its own right.
    #
    # `Payload` is a plain class rather than a pydantic type, so it has to be allowed
    # through as is. The rest of the configuration is inherited, `extra="forbid"`
    # included.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: UUID4
    # `exclude=True` keeps the payload out of `to_json` and `model_dump_json` in one
    # place, so no message needs a hand written serializer that remembers to omit it.
    payload: Annotated[Payload | None, BeforeValidator(_wrap_payload)] = Field(
        default=None, exclude=True
    )

    @classmethod
    def from_json(
        cls,
        message_json: str | bytes | bytearray | Mapping[str, JsonValue],
        payload: Payload | bytes | bytearray | None = None,
    ) -> Self:
        """Validate JSON reported by an agent into this message, attaching its payload.

        The counterpart to `to_json`, for a listener whose agents speak the framework's
        JSON. A listener with a wire format of its own parses that format and constructs
        the message directly instead.

        Args:
            message_json: The message as raw JSON text or bytes, or as an already
                decoded JSON object.
            payload: The binary payload received alongside the JSON, if any.

        Raises:
            ValueError: If the JSON cannot be decoded, is not an object, carries an
                unexpected key, supplies a `payload` key, or fails field validation.

        Returns:
            The validated message, with the payload attached.
        """
        message = super().from_json(message_json)
        if payload is not None:
            message.payload = _wrap_payload(payload)
        return message


class RegistrationMessageModel(_Message):
    """Registration details reported by an agent when it first contacts a listener.

    Every field is self-reported by the agent and none of it is verified by the server,
    so treat the contents as claims about the host rather than as facts. That includes
    `endpoint` and `remote_ip`: a listener that observes a usable peer address should
    supply it only where the agent left those unset.

    Attributes:
        payload_id: The ID of the payload the agent was generated from. Either this or
            `agent_type` must be provided, but not both.
        agent_type: The name of the agent type to register as. Either this or `payload_id`
            must be provided, but not both.
        user: The OS username the agent process is running as.
        is_admin: Whether the agent is running with administrator or root privileges.
        os: The name of the host operating system, for example "Windows".
        version: The version string of the host operating system.
        arch: The CPU architecture of the host system, for example "x86_64".
        pid: The process ID of the agent on its host.
        locale: The locale string of the host system, for example "en_US".
        local_ip: The local IP address of the agent's host as seen by the agent itself.
        hostname: The hostname of the agent's host.
        endpoint: A human-readable string identifying the agent's network endpoint.
        remote_ip: The IP address the agent is reachable at.
        agent_data: A dictionary containing additional data about the agent.
    """

    payload_id: UUID4 | None = None
    agent_type: str | None = None
    user: str | None = None
    is_admin: bool | None = None
    os: str | None = None
    version: str | None = None
    arch: str | None = None
    pid: int | None = None
    locale: str | None = None
    local_ip: str | None = None
    hostname: str | None = None
    endpoint: str = ""
    remote_ip: str | None = None
    agent_data: dict[str, JsonValue] | None = None

    @model_validator(mode="after")
    def _require_payload_id_or_agent_type(self) -> RegistrationMessageModel:
        # An agent identifies itself by exactly one of the two: the payload it was built
        # from, or the agent type it claims to be. Neither leaves the agent type
        # unresolvable, and both is ambiguous.
        if (self.payload_id is None) == (self.agent_type is None):
            raise ValueError(
                "exactly one of 'payload_id' or 'agent_type' must be provided"
            )
        return self


class RegistrationResponseMessageModel(_Message):
    """The response to a registration, carrying the agent's assigned ID.

    Attributes:
        agent_id: The identifier assigned to the newly registered agent.
    """

    agent_id: UUID4


class TaskLaunchMessageModel(_TaskMessage):
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

    command: str
    arguments: dict[str, JsonValue] = {}
    data: dict[str, JsonValue] = {}


class TaskInputMessageModel(_TaskMessage):
    """Message sent to an agent to provide additional input to a running task.

    Used when a task requires interactive or incremental input after the initial
    launch message has been sent.

    Attributes:
        task_id: Unique identifier of the task receiving the input.
        data: Structured input data for the running task. Must be JSON-serializable.
        payload: Optional binary payload accompanying the input, such as a file chunk
            or continuation data.
    """

    data: dict[str, JsonValue] = {}


class TaskOutputMessageModel(_TaskMessage):
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

    success: bool
    message: str = ""
    data: dict[str, JsonValue] = {}

    def to_outcome(self) -> Success | Failure:
        """Convert the message into a Success or Failure outcome object.

        Returns:
            A Success instance if success is True, otherwise a Failure instance.
        """

        if self.success:
            return Success(task_output_message=self)
        else:
            return Failure(task_output_message=self)
