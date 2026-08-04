import asyncio
import pathlib
import uuid
from functools import wraps
from typing import TYPE_CHECKING, Any, BinaryIO, Literal, TextIO

from loguru import logger
from pydantic import JsonValue

from consortium.framework.event_hooks.event_type import EventType
from consortium.server.models.listener_and_agent_reference_models import (
    PersistentAgentReferenceModel,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.artifact_objects import Artifact
from consortium.server.services.events_service import EventsService
from consortium.server.services.repository_service import RepositoryService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    run_async_background_task,
)

if TYPE_CHECKING:
    from consortium.server.services.agents_service import AgentsService

# Sentinel distinguishing "leave the artifact's stored data untouched" from an explicit
# request to rebuild it. This matters because `agent_id=None` is itself a meaningful
# value (an artifact attributed to no producing agent), so it cannot double as "do not
# update the data".
_UNSET: Any = object()


class ArtifactsService:
    def __init__(
        self,
        events_service: EventsService,
        repository_service: RepositoryService,
        agents_service: AgentsService,
    ):
        self._events_service = events_service
        self._repository_service = repository_service
        # The agents service is used to resolve an agent ID into a stored agent reference
        # when attributing a producing agent to an artifact.
        self._agents_service = agents_service
        self.repository_directory_path = repository_service.repository_directory_path
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Artifacts Service"

    def __repr__(self) -> str:
        return f"ArtifactsService(repository_service={self._repository_service!r})"

    def _build_artifact_resource_data(
        self,
        agent_id: str | uuid.UUID | None,
    ) -> dict[str, JsonValue]:
        # Attribution of a producing agent is optional. When no agent ID is provided (for
        # example an artifact created directly by a plugin rather than through the agent
        # file manager service) the reference is stored as `None`. This data is persisted
        # in the `data` field of the artifact's repository resource and validated against
        # `ArtifactDataModel` at the API boundary.
        if agent_id is None:
            return {"agent": None}

        agent = self._agents_service.get_agent_by_agent_id(agent_id=agent_id)
        # The persistent reference is built here rather than from the agent's own
        # `to_json_reference`, which is the live form embedding the full agent type
        # descriptor. Only the agent type's name is recorded: the descriptor itself
        # belongs to the live agent type registry and would go stale once on disk.
        agent_reference = PersistentAgentReferenceModel(
            agent_id=str(agent.agent_id),
            name=agent.name,
            agent_type=agent.agent_type.name,
        )
        return {"agent": agent_reference.model_dump(mode="json")}

    # @wraps copies function docstring information over to avoid rewriting it, used for
    # boilerplate forwarding methods that don't do anything meaningfully different. We
    # still need to include some docstring pointing to the forwarded method since
    # mkdocstrings' griffe analyzer only does static analysis when generating
    # documentation
    @wraps(RepositoryService.load_repository_metadata)
    @log_and_propagate_error_on_service_method
    def load_repository_metadata(self) -> None:
        """See [`RepositoryService.load_repository_metadata`][consortium.server.services.repository_service.RepositoryService.load_repository_metadata]."""
        self._repository_service.load_repository_metadata()
        self._logger.debug("Loaded artifacts repository metadata")

    @wraps(RepositoryService.save_repository_metadata)
    @log_and_propagate_error_on_service_method
    def save_repository_metadata(self) -> None:
        """See [`RepositoryService.save_repository_metadata`][consortium.server.services.repository_service.RepositoryService.save_repository_metadata]."""
        self._repository_service.save_repository_metadata()

    @log_and_propagate_error_on_service_method
    def reserve_resource_id(self) -> uuid.UUID:
        """Reserves and returns a new resource ID without creating any artifact.

        The returned ID can later be passed as `resource_id` to one of the artifact
        creation methods to claim it. Reserving an ID up front lets a caller learn the
        artifact's ID before its file or directory exists on disk (for example to embed
        the ID inside the content that will be stored).

        Returns:
            The freshly reserved resource ID, unique across the repository.
        """
        resource_id = self._repository_service.reserve_resource_id()
        self._logger.debug("Reserved resource ID '{}'", str(resource_id))
        return resource_id

    @log_and_propagate_error_on_service_method
    async def create_artifact_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        agent_id: str | uuid.UUID | None = None,
    ) -> Artifact:
        """Creates a new artifact file from in-memory or streamed content.

        The content is written to a new file on disk in the artifacts repository and an
        `ARTIFACT_CREATED` event is emitted. When an `agent_id` is supplied the producing
        agent is resolved and recorded against the artifact for attribution.

        Args:
            content: The content to write into the new
                artifact file, supplied either directly as text/bytes or as an open
                text/binary stream to read the content from.
            name: A human-readable display name for the artifact. When
                `None`, the artifact's generated UUID is used as its name.
            description: A short human-readable description of the artifact.
                Defaults to an empty string when omitted.
            resource_id: A previously reserved resource ID to
                claim for this artifact. When `None`, a new ID is generated automatically.
            agent_id: The ID of the agent that produced this
                artifact, recorded for attribution. When `None`, the artifact is stored
                with no producing agent.

        Returns:
            The newly created artifact file resource.

        Raises:
            AgentNotFoundError: If `agent_id` is provided but no agent with that ID is
                registered.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
        """
        artifact = await asyncio.to_thread(
            self._repository_service.create_file,
            content=content,
            name=name,
            description=description,
            resource_id=resource_id,
            data=self._build_artifact_resource_data(agent_id=agent_id),
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_CREATED,
                message=f"Created artifact: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Created artifact file: {!r}", artifact)
        return Artifact(resource=artifact, agents_service=self._agents_service)

    @log_and_propagate_error_on_service_method
    async def add_artifact_file(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
        agent_id: str | uuid.UUID | None = None,
    ) -> Artifact:
        """Registers an existing file on disk as an artifact.

        Unlike `create_artifact_file`, no new content is written: the file at `path` is
        moved (or copied when `copy=True`) into the artifacts repository, registered as a
        resource, and an `ARTIFACT_CREATED` event is emitted. When an `agent_id` is
        supplied the producing agent is resolved and recorded for attribution.

        Args:
            path: Filesystem path to the existing file to ingest as
                an artifact.
            name: A human-readable display name for the artifact. When
                `None`, the original filename is used.
            description: A short human-readable description of the artifact.
                Defaults to an empty string when omitted.
            resource_id: A previously reserved resource ID to
                claim for this artifact. When `None`, a new ID is generated automatically.
            copy: When `False` (default) the source file is moved into the
                repository, leaving nothing at the original path. When `True` the source
                file is copied and the original is left in place.
            agent_id: The ID of the agent that produced this
                artifact, recorded for attribution. When `None`, the artifact is stored
                with no producing agent.

        Returns:
            The newly registered artifact file resource.

        Raises:
            AgentNotFoundError: If `agent_id` is provided but no agent with that ID is
                registered.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
        """
        artifact = await asyncio.to_thread(
            self._repository_service.add_file,
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
            data=self._build_artifact_resource_data(agent_id=agent_id),
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_CREATED,
                message=f"Added artifact: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Added artifact file: {!r}", artifact)
        return Artifact(resource=artifact, agents_service=self._agents_service)

    @log_and_propagate_error_on_service_method
    async def create_artifact_directory(
        self,
        content: bytes | BinaryIO | str | pathlib.Path | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"]
        | None = None,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        agent_id: str | uuid.UUID | None = None,
    ) -> Artifact:
        """Creates a new artifact directory, optionally populated from existing content.

        An empty directory is created on disk in the artifacts repository, or, when
        `content` is provided, it is populated from that content. How `content` is
        interpreted depends on its type: raw bytes and open binary streams are unpacked
        as archive content using `archive_file_format`, while a `str` or `pathlib.Path`
        is treated as a path to an existing source directory whose tree is copied in. An
        `ARTIFACT_CREATED` event is emitted. When an `agent_id` is supplied the producing
        agent is resolved and recorded for attribution.

        Args:
            content: Archive content to unpack into the new directory, supplied as raw
                bytes or an open binary stream, or a path to an existing source directory
                to copy in. When `None`, an empty directory is created.
            archive_file_format: The archive format used to interpret `content` when
                unpacking. Must be set whenever `content` is archive content; ignored
                when `content` is a source directory path or `None`.
            name: A human-readable display name for the artifact. When
                `None`, the artifact's generated UUID is used as its name.
            description: A short human-readable description of the artifact.
                Defaults to an empty string when omitted.
            resource_id: A previously reserved resource ID to
                claim for this artifact. When `None`, a new ID is generated automatically.
            agent_id: The ID of the agent that produced this
                artifact, recorded for attribution. When `None`, the artifact is stored
                with no producing agent.

        Returns:
            The newly created artifact directory resource.

        Raises:
            AgentNotFoundError: If `agent_id` is provided but no agent with that ID is
                registered.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
            InvalidRepositoryDirectoryArchiveFileFormatError: If `content` is archive
                content that cannot be unpacked as `archive_file_format`, or if
                `archive_file_format` is not set.
        """
        artifact = await asyncio.to_thread(
            self._repository_service.create_directory,
            content=content,
            archive_file_format=archive_file_format,
            name=name,
            description=description,
            resource_id=resource_id,
            data=self._build_artifact_resource_data(agent_id=agent_id),
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_CREATED,
                message=f"Created artifact directory: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Created artifact directory: {!r}", artifact)
        return Artifact(resource=artifact, agents_service=self._agents_service)

    @log_and_propagate_error_on_service_method
    async def add_artifact_directory(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
        agent_id: str | uuid.UUID | None = None,
    ) -> Artifact:
        """Registers an existing directory on disk as an artifact.

        Unlike `create_artifact_directory`, no new directory is created: the directory at
        `path` is moved (or copied when `copy=True`) into the artifacts repository,
        registered as a resource, and an `ARTIFACT_CREATED` event is emitted. When an
        `agent_id` is supplied the producing agent is resolved and recorded for
        attribution.

        Args:
            path: Filesystem path to the existing directory to ingest
                as an artifact.
            name: A human-readable display name for the artifact. When
                `None`, the original directory name is used.
            description: A short human-readable description of the artifact.
                Defaults to an empty string when omitted.
            resource_id: A previously reserved resource ID to
                claim for this artifact. When `None`, a new ID is generated automatically.
            copy: When `False` (default) the source directory is moved into the
                repository, leaving nothing at the original path. When `True` the source
                directory is copied and the original is left in place.
            agent_id: The ID of the agent that produced this
                artifact, recorded for attribution. When `None`, the artifact is stored
                with no producing agent.

        Returns:
            The newly registered artifact directory resource.

        Raises:
            AgentNotFoundError: If `agent_id` is provided but no agent with that ID is
                registered.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
        """
        artifact = await asyncio.to_thread(
            self._repository_service.add_directory,
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
            data=self._build_artifact_resource_data(agent_id=agent_id),
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_CREATED,
                message=f"Added artifact directory: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Added artifact directory: {!r}", artifact)
        return Artifact(resource=artifact, agents_service=self._agents_service)

    @log_and_propagate_error_on_service_method
    async def update_artifact_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        agent_id: str | uuid.UUID | None = _UNSET,
    ) -> Artifact:
        """Updates an artifact's mutable metadata.

        `name` and `description` are updated in place when provided. The artifact's stored
        `data` is only rebuilt when `agent_id` is passed, mirroring the attribution
        parameter of the artifact creation methods: the given agent is resolved into a
        stored reference exactly as it would be on creation. When `agent_id` is omitted the
        existing `data` is left untouched. An `ARTIFACT_UPDATED` event is emitted.

        Args:
            resource_id: The ID of the artifact to update.
            name: A new human-readable display name for the artifact. When `None`, the
                existing name is preserved.
            description: A new description for the artifact. When `None`, the existing
                description is preserved.
            agent_id: When provided, rebuilds the artifact's attribution data from this
                agent ID (or clears attribution when `None`). When omitted entirely, the
                artifact's existing data is left unchanged.

        Returns:
            The updated artifact resource.

        Raises:
            ResourceNotFoundError: If no artifact with the given ID exists.
            AgentNotFoundError: If `agent_id` is provided but no agent with that ID is
                registered.
        """
        data = None
        if agent_id is not _UNSET:
            data = self._build_artifact_resource_data(agent_id=agent_id)

        artifact = await asyncio.to_thread(
            self._repository_service.update_resource_by_resource_id,
            resource_id=resource_id,
            name=name,
            description=description,
            data=data,
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_UPDATED,
                message=f"Updated artifact: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Updated artifact: {!r}", artifact)
        return Artifact(resource=artifact, agents_service=self._agents_service)

    @log_and_propagate_error_on_service_method
    async def delete_artifact_by_resource_id(
        self, resource_id: str | uuid.UUID
    ) -> None:
        """Deletes an artifact from disk and the repository.

        The artifact's metadata is snapshotted before removal so it can be carried on the
        emitted `ARTIFACT_DELETED` event, then the resource is deleted from disk and
        deregistered.

        Args:
            resource_id: The ID of the artifact to delete.

        An artifact whose file or directory is already missing from the repository
        directory is deleted successfully: the record is deregistered and the event is
        still emitted.

        Raises:
            ResourceNotFoundError: If no artifact with the given ID exists.
        """
        # Snapshot JSON before deletion since to_json() reads from disk
        artifact = self._repository_service.get_resource_by_resource_id(
            resource_id=resource_id
        )
        artifact_json = artifact.to_json()
        await asyncio.to_thread(
            self._repository_service.delete_resource_by_resource_id,
            resource_id=resource_id,
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_DELETED,
                message=f"Deleted artifact: {resource_id}",
                data=artifact_json,
            )
        )
        self._logger.debug("Deleted artifact: {}", str(resource_id))

    @log_and_propagate_error_on_service_method
    def get_all_artifacts(self) -> list[Artifact]:
        """Returns every artifact currently tracked by the artifacts service.

        Returns:
            A list of all artifacts, covering both file and directory artifacts, each
                wrapping its repository resource. Empty if no artifacts exist.
        """
        artifacts = self._repository_service.get_all_resources()
        self._logger.debug(
            "Retrieved all artifacts ({} artifact(s) retrieved)",
            len(artifacts),
        )
        return [
            Artifact(resource=artifact, agents_service=self._agents_service)
            for artifact in artifacts
        ]

    @log_and_propagate_error_on_service_method
    def get_artifact_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> Artifact:
        """Returns a single artifact by its ID.

        Args:
            resource_id: The ID of the artifact to retrieve.

        Returns:
            The requested artifact resource, either a file or a directory depending
                on how it was created.

        Raises:
            ResourceNotFoundError: If no artifact with the given ID exists.
        """
        artifact = self._repository_service.get_resource_by_resource_id(
            resource_id=resource_id
        )
        self._logger.debug("Retrieved artifact: {!r}", artifact)
        return Artifact(resource=artifact, agents_service=self._agents_service)
