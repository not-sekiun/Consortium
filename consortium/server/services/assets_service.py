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


class AssetsService:
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
        return "Assets Service"

    def __repr__(self) -> str:
        return f"AssetsService(repository_service={self._repository_service!r})"

    @log_and_propagate_error_on_service_method
    def load_repository_metadata(self) -> None:
        self._repository_service.load_repository_metadata()
        self._logger.debug("Loaded assets repository metadata")

    @log_and_propagate_error_on_service_method
    def save_repository_metadata(self) -> None:
        self._repository_service.save_repository_metadata()

    @log_and_propagate_error_on_service_method
    def reserve_asset_id(self) -> uuid.UUID:
        asset_id = self._repository_service.reserve_resource_id()
        self._logger.debug("Reserved asset ID '{}'", str(asset_id))
        return asset_id

    @log_and_propagate_error_on_service_method
    def create_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
    ) -> RepositoryFile:
        asset = self._repository_service.create_file(
            content=content,
            name=name,
            description=description,
            resource_id=resource_id,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_CREATED,
                message=f"Created asset: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Created asset file: {!r}", asset)
        return asset

    @log_and_propagate_error_on_service_method
    def add_file(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
    ) -> RepositoryFile:
        asset = self._repository_service.add_file(
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_CREATED,
                message=f"Added asset: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Added asset file: {!r}", asset)
        return asset

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
        asset = self._repository_service.create_directory(
            content=content,
            archive_file_format=archive_file_format,
            name=name,
            description=description,
            resource_id=resource_id,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_CREATED,
                message=f"Created asset directory: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Created asset directory: {!r}", asset)
        return asset

    @log_and_propagate_error_on_service_method
    def add_directory(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
    ) -> RepositoryDirectory:
        asset = self._repository_service.add_directory(
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_CREATED,
                message=f"Added asset directory: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Added asset directory: {!r}", asset)
        return asset

    @log_and_propagate_error_on_service_method
    def delete_asset_by_asset_id(self, asset_id: str | uuid.UUID) -> None:
        # Snapshot JSON before deletion since to_json() reads from disk
        asset = self._repository_service.get_resource_by_resource_id(
            resource_id=asset_id
        )
        asset_json = asset.to_json()
        self._repository_service.delete_resource_by_resource_id(resource_id=asset_id)
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_DELETED,
                message=f"Deleted asset: {asset_id}",
                data=asset_json,
            )
        )
        self._logger.debug("Deleted asset: {}", str(asset_id))

    @log_and_propagate_error_on_service_method
    def get_all_assets(self) -> list[RepositoryFile | RepositoryDirectory]:
        assets = self._repository_service.get_all_resources()
        self._logger.debug(
            "Retrieved all assets ({} asset(s) retrieved)",
            len(assets),
        )
        return assets

    @log_and_propagate_error_on_service_method
    def get_asset_by_asset_id(
        self,
        asset_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        asset = self._repository_service.get_resource_by_resource_id(
            resource_id=asset_id
        )
        self._logger.debug("Retrieved asset: {!r}", asset)
        return asset
