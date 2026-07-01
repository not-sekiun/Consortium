import asyncio
import pathlib
import uuid
from typing import BinaryIO, Literal, TextIO

from loguru import logger

from consortium.framework.event_hooks.event_type import EventType
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)
from consortium.server.services.events_service import EventsService
from consortium.server.services.repository_service import RepositoryService
from consortium.server.utils import log_and_propagate_error_on_service_method


class ArtifactsService:
    def __init__(
        self,
        events_service: EventsService,
        repository_service: RepositoryService,
    ):
        self._events_service = events_service
        self._repository_service = repository_service
        self.repository_directory_path = repository_service.repository_directory_path
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Artifacts Service"

    def __repr__(self) -> str:
        return f"ArtifactsService(repository_service={self._repository_service!r})"

    @log_and_propagate_error_on_service_method
    def load_repository_metadata(self) -> None:
        self._repository_service.load_repository_metadata()
        self._logger.debug("Loaded artifacts repository metadata")

    @log_and_propagate_error_on_service_method
    def save_repository_metadata(self) -> None:
        self._repository_service.save_repository_metadata()

    @log_and_propagate_error_on_service_method
    def reserve_artifact_id(self) -> uuid.UUID:
        artifact_id = self._repository_service.reserve_resource_id()
        self._logger.debug("Reserved artifact ID '{}'", str(artifact_id))
        return artifact_id

    @log_and_propagate_error_on_service_method
    def create_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
    ) -> RepositoryFile:
        artifact = self._repository_service.create_file(
            content=content,
            name=name,
            description=description,
            resource_id=resource_id,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_CREATED,
                message=f"Created artifact: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Created artifact file: {!r}", artifact)
        return artifact

    @log_and_propagate_error_on_service_method
    def add_file(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
    ) -> RepositoryFile:
        artifact = self._repository_service.add_file(
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_CREATED,
                message=f"Added artifact: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Added artifact file: {!r}", artifact)
        return artifact

    @log_and_propagate_error_on_service_method
    def create_directory(
        self,
        content: bytes | BinaryIO | str | pathlib.Path | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"]
        | None = None,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
    ) -> RepositoryDirectory:
        artifact = self._repository_service.create_directory(
            content=content,
            archive_file_format=archive_file_format,
            name=name,
            description=description,
            resource_id=resource_id,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_CREATED,
                message=f"Created artifact directory: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Created artifact directory: {!r}", artifact)
        return artifact

    @log_and_propagate_error_on_service_method
    def add_directory(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
    ) -> RepositoryDirectory:
        artifact = self._repository_service.add_directory(
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_CREATED,
                message=f"Added artifact directory: {artifact.resource_id}",
                data=artifact.to_json(),
            )
        )
        self._logger.debug("Added artifact directory: {!r}", artifact)
        return artifact

    @log_and_propagate_error_on_service_method
    def delete_artifact_by_artifact_id(self, artifact_id: str | uuid.UUID) -> None:
        # Snapshot JSON before deletion since to_json() reads from disk
        artifact = self._repository_service.get_resource_by_resource_id(
            resource_id=artifact_id
        )
        artifact_json = artifact.to_json()
        self._repository_service.delete_resource_by_resource_id(resource_id=artifact_id)
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ARTIFACT_DELETED,
                message=f"Deleted artifact: {artifact_id}",
                data=artifact_json,
            )
        )
        self._logger.debug("Deleted artifact: {}", str(artifact_id))

    @log_and_propagate_error_on_service_method
    def get_all_artifacts(self) -> list[RepositoryFile | RepositoryDirectory]:
        artifacts = self._repository_service.get_all_resources()
        self._logger.debug(
            "Retrieved all artifacts ({} artifact(s) retrieved)",
            len(artifacts),
        )
        return artifacts

    @log_and_propagate_error_on_service_method
    def get_artifact_by_artifact_id(
        self,
        artifact_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        artifact = self._repository_service.get_resource_by_resource_id(
            resource_id=artifact_id
        )
        self._logger.debug("Retrieved artifact: {!r}", artifact)
        return artifact
