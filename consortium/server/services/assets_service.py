import asyncio
import pathlib
import uuid
from functools import wraps
from typing import TYPE_CHECKING, Any, BinaryIO, Literal, TextIO

from loguru import logger
from pydantic import JsonValue

from consortium.framework.event_hooks.event_type import EventType
from consortium.server.models.logging_models import LoggerType
from consortium.server.models.user_account_models import (
    PersistentUserAccountReferenceModel,
)
from consortium.server.objects.asset_objects import Asset
from consortium.server.services.events_service import EventsService
from consortium.server.services.repository_service import RepositoryService
from consortium.server.utils import log_and_propagate_error_on_service_method

if TYPE_CHECKING:
    from consortium.server.services.user_accounts_service import UserAccountsService

# Sentinel distinguishing "leave the asset's stored data untouched" from an explicit
# request to rebuild it. This matters because `user_account_id=None` is itself a
# meaningful value (an asset attributed to no uploading user account), so it cannot
# double as "do not update the data".
_UNSET: Any = object()


class AssetsService:
    def __init__(
        self,
        events_service: EventsService,
        repository_service: RepositoryService,
        user_accounts_service: UserAccountsService,
    ):
        self._events_service = events_service
        self._repository_service = repository_service
        # The user accounts service is used to resolve a user account ID into a stored
        # user account reference when attributing an uploading user account to an asset.
        self._user_accounts_service = user_accounts_service
        self.repository_directory_path = repository_service.repository_directory_path
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Assets Service"

    def __repr__(self) -> str:
        return f"AssetsService(repository_service={self._repository_service!r})"

    def _build_asset_resource_data(
        self,
        user_account_id: str | uuid.UUID | None,
    ) -> dict[str, JsonValue]:
        # Attribution of an uploading user account is optional. When no user account ID
        # is provided (for example an asset created directly by a plugin) the reference
        # is stored as `None`. This data is persisted in the `data` field of the asset's
        # repository resource and validated against `AssetDataModel` at the API boundary.
        if user_account_id is None:
            return {"user_account": None}

        user_account = self._user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
        user_account_reference = PersistentUserAccountReferenceModel(
            username=user_account.username,
            role=user_account.role,
        )
        return {
            "user_account": user_account_reference.model_dump(mode="json"),
        }

    @wraps(RepositoryService.load_repository_metadata)
    @log_and_propagate_error_on_service_method
    def load_repository_metadata(self) -> None:
        """Loads the assets repository metadata from disk into memory.

        Delegates to the underlying repository service, reconstructing the in-memory
        record of every tracked asset from the repository metadata file. If the metadata
        file does not yet exist an empty one is created.

        Raises:
            InvalidRepositoryMetadataFileJSONError: If the metadata file contains
                invalid JSON.
            InvalidRepositoryMetadataFileSchemaError: If the metadata file does not
                follow the expected schema.
            UnsyncedRepositoryMetadataFileError: If a resource recorded in the metadata
                file does not exist on disk.
        """
        self._repository_service.load_repository_metadata()
        self._logger.debug("Loaded assets repository metadata")

    @wraps(RepositoryService.save_repository_metadata)
    @log_and_propagate_error_on_service_method
    def save_repository_metadata(self) -> None:
        """Persists the current in-memory assets repository metadata to disk.

        Delegates to the underlying repository service, writing the metadata for every
        tracked asset to the repository metadata file as JSON.
        """
        self._repository_service.save_repository_metadata()

    @log_and_propagate_error_on_service_method
    def reserve_resource_id(self) -> uuid.UUID:
        """Reserves and returns a new resource ID without creating any asset.

        The returned ID can later be passed as `resource_id` to one of the asset
        creation methods to claim it. Reserving an ID up front lets a caller learn the
        asset's ID before its file or directory exists on disk (for example to embed the
        ID inside the content that will be stored).

        Returns:
            The freshly reserved resource ID, unique across the repository.
        """
        resource_id = self._repository_service.reserve_resource_id()
        self._logger.debug("Reserved resource ID '{}'", str(resource_id))
        return resource_id

    @log_and_propagate_error_on_service_method
    async def create_asset_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        user_account_id: str | uuid.UUID | None = None,
    ) -> Asset:
        """Creates a new asset file from in-memory or streamed content.

        The content is written to a new file on disk in the assets repository and an
        `ASSET_CREATED` event is emitted. When a `user_account_id` is supplied the
        uploading user account is resolved and recorded against the asset for
        attribution.

        Args:
            content: The content to write into the new asset file, supplied either
                directly as text/bytes or as an open text/binary stream to read the
                content from.
            name: A human-readable display name for the asset. When `None`, the asset's
                generated UUID is used as its name.
            description: A short human-readable description of the asset. Defaults to an
                empty string when omitted.
            resource_id: A previously reserved resource ID to claim for this asset. When
                `None`, a new ID is generated automatically.
            user_account_id: The ID of the user account that uploaded this asset,
                recorded for attribution. When `None`, the asset is stored with no
                uploading user account.

        Returns:
            The newly created asset file resource.

        Raises:
            UserAccountIDNotFoundError: If `user_account_id` is provided but no user
                account with that ID exists.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
        """
        asset = await asyncio.to_thread(
            self._repository_service.create_file,
            content=content,
            name=name,
            description=description,
            resource_id=resource_id,
            data=self._build_asset_resource_data(user_account_id=user_account_id),
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_CREATED,
                message=f"Created asset: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Created asset file: {!r}", asset)
        return Asset(resource=asset, user_accounts_service=self._user_accounts_service)

    @log_and_propagate_error_on_service_method
    async def add_asset_file(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
        user_account_id: str | uuid.UUID | None = None,
    ) -> Asset:
        """Registers an existing file on disk as an asset.

        Unlike `create_asset_file`, no new content is written: the file at `path` is
        moved (or copied when `copy=True`) into the assets repository, registered as a
        resource, and an `ASSET_CREATED` event is emitted. When a `user_account_id` is
        supplied the uploading user account is resolved and recorded for attribution.

        Args:
            path: Filesystem path to the existing file to ingest as an asset.
            name: A human-readable display name for the asset. When `None`, the original
                filename is used.
            description: A short human-readable description of the asset. Defaults to an
                empty string when omitted.
            resource_id: A previously reserved resource ID to claim for this asset. When
                `None`, a new ID is generated automatically.
            copy: When `False` (default) the source file is moved into the repository,
                leaving nothing at the original path. When `True` the source file is
                copied and the original is left in place.
            user_account_id: The ID of the user account that uploaded this asset,
                recorded for attribution. When `None`, the asset is stored with no
                uploading user account.

        Returns:
            The newly registered asset file resource.

        Raises:
            UserAccountIDNotFoundError: If `user_account_id` is provided but no user
                account with that ID exists.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
        """
        asset = await asyncio.to_thread(
            self._repository_service.add_file,
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
            data=self._build_asset_resource_data(user_account_id=user_account_id),
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_CREATED,
                message=f"Added asset: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Added asset file: {!r}", asset)
        return Asset(resource=asset, user_accounts_service=self._user_accounts_service)

    @log_and_propagate_error_on_service_method
    async def create_asset_directory(
        self,
        content: bytes | BinaryIO | str | pathlib.Path | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"]
        | None = None,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        user_account_id: str | uuid.UUID | None = None,
    ) -> Asset:
        """Creates a new asset directory, optionally populated from an archive.

        An empty directory is created on disk in the assets repository, or, when
        `content` and `archive_file_format` are provided, the archive content is
        extracted into it. An `ASSET_CREATED` event is emitted. When a `user_account_id`
        is supplied the uploading user account is resolved and recorded for attribution.

        Args:
            content: Archive content to extract into the new directory, supplied as raw
                bytes, an open binary stream, or a path to an archive file. When `None`,
                an empty directory is created.
            archive_file_format: The archive format used to interpret `content` when
                extracting. Must be set whenever `content` is provided; ignored when
                `content` is `None`.
            name: A human-readable display name for the asset. When `None`, the asset's
                generated UUID is used as its name.
            description: A short human-readable description of the asset. Defaults to an
                empty string when omitted.
            resource_id: A previously reserved resource ID to claim for this asset. When
                `None`, a new ID is generated automatically.
            user_account_id: The ID of the user account that uploaded this asset,
                recorded for attribution. When `None`, the asset is stored with no
                uploading user account.

        Returns:
            The newly created asset directory resource.

        Raises:
            UserAccountIDNotFoundError: If `user_account_id` is provided but no user
                account with that ID exists.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
        """
        asset = await asyncio.to_thread(
            self._repository_service.create_directory,
            content=content,
            archive_file_format=archive_file_format,
            name=name,
            description=description,
            resource_id=resource_id,
            data=self._build_asset_resource_data(user_account_id=user_account_id),
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_CREATED,
                message=f"Created asset directory: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Created asset directory: {!r}", asset)
        return Asset(resource=asset, user_accounts_service=self._user_accounts_service)

    @log_and_propagate_error_on_service_method
    async def add_asset_directory(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        resource_id: str | uuid.UUID | None = None,
        copy: bool = False,
        user_account_id: str | uuid.UUID | None = None,
    ) -> Asset:
        """Registers an existing directory on disk as an asset.

        Unlike `create_asset_directory`, no new directory is created: the directory at
        `path` is moved (or copied when `copy=True`) into the assets repository,
        registered as a resource, and an `ASSET_CREATED` event is emitted. When a
        `user_account_id` is supplied the uploading user account is resolved and recorded
        for attribution.

        Args:
            path: Filesystem path to the existing directory to ingest as an asset.
            name: A human-readable display name for the asset. When `None`, the original
                directory name is used.
            description: A short human-readable description of the asset. Defaults to an
                empty string when omitted.
            resource_id: A previously reserved resource ID to claim for this asset. When
                `None`, a new ID is generated automatically.
            copy: When `False` (default) the source directory is moved into the
                repository, leaving nothing at the original path. When `True` the source
                directory is copied and the original is left in place.
            user_account_id: The ID of the user account that uploaded this asset,
                recorded for attribution. When `None`, the asset is stored with no
                uploading user account.

        Returns:
            The newly registered asset directory resource.

        Raises:
            UserAccountIDNotFoundError: If `user_account_id` is provided but no user
                account with that ID exists.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
                corresponding reservation.
        """
        asset = await asyncio.to_thread(
            self._repository_service.add_directory,
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
            data=self._build_asset_resource_data(user_account_id=user_account_id),
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_CREATED,
                message=f"Added asset directory: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Added asset directory: {!r}", asset)
        return Asset(resource=asset, user_accounts_service=self._user_accounts_service)

    @log_and_propagate_error_on_service_method
    async def update_asset_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        user_account_id: str | uuid.UUID | None = _UNSET,
    ) -> Asset:
        """Updates an asset's mutable metadata.

        `name` and `description` are updated in place when provided. The asset's stored
        `data` is only rebuilt when `user_account_id` is passed, mirroring the attribution
        parameter of the asset creation methods: the given user account is resolved into a
        stored reference exactly as it would be on creation. When `user_account_id` is
        omitted the existing `data` is left untouched. An `ASSET_UPDATED` event is emitted.

        Args:
            resource_id: The ID of the asset to update.
            name: A new human-readable display name for the asset. When `None`, the
                existing name is preserved.
            description: A new description for the asset. When `None`, the existing
                description is preserved.
            user_account_id: When provided, rebuilds the asset's attribution data from
                this user account ID (or clears attribution when `None`). When omitted
                entirely, the asset's existing data is left unchanged.

        Returns:
            The updated asset resource.

        Raises:
            RepositoryResourceNotFoundError: If no asset with the given ID exists.
            UserAccountIDNotFoundError: If `user_account_id` is provided but no user
                account with that ID exists.
        """
        data = None
        if user_account_id is not _UNSET:
            data = self._build_asset_resource_data(user_account_id=user_account_id)

        asset = await asyncio.to_thread(
            self._repository_service.update_resource_by_resource_id,
            resource_id=resource_id,
            name=name,
            description=description,
            data=data,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_UPDATED,
                message=f"Updated asset: {asset.resource_id}",
                data=asset.to_json(),
            )
        )
        self._logger.debug("Updated asset: {!r}", asset)
        return Asset(resource=asset, user_accounts_service=self._user_accounts_service)

    @log_and_propagate_error_on_service_method
    async def delete_asset_by_resource_id(self, resource_id: str | uuid.UUID) -> None:
        """Deletes an asset from disk and the repository.

        The asset's metadata is snapshotted before removal so it can be carried on the
        emitted `ASSET_DELETED` event, then the resource is deleted from disk and
        deregistered.

        Args:
            resource_id: The ID of the asset to delete.

        Raises:
            RepositoryResourceNotFoundError: If no asset with the given ID exists.
        """
        # Snapshot JSON before deletion since to_json() reads from disk
        asset = self._repository_service.get_resource_by_resource_id(
            resource_id=resource_id
        )
        asset_json = asset.to_json()
        await asyncio.to_thread(
            self._repository_service.delete_resource_by_resource_id,
            resource_id=resource_id,
        )
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.ASSET_DELETED,
                message=f"Deleted asset: {resource_id}",
                data=asset_json,
            )
        )
        self._logger.debug("Deleted asset: {}", str(resource_id))

    @log_and_propagate_error_on_service_method
    def get_all_assets(self) -> list[Asset]:
        """Returns every asset currently tracked by the assets service.

        Returns:
            A list of all assets, covering both file and directory assets, each wrapping
                its repository resource. Empty if no assets exist.
        """
        assets = self._repository_service.get_all_resources()
        self._logger.debug(
            "Retrieved all assets ({} asset(s) retrieved)",
            len(assets),
        )
        return [
            Asset(resource=asset, user_accounts_service=self._user_accounts_service)
            for asset in assets
        ]

    @log_and_propagate_error_on_service_method
    def get_asset_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
    ) -> Asset:
        """Returns a single asset by its ID.

        Args:
            resource_id: The ID of the asset to retrieve.

        Returns:
            The requested asset resource, either a file or a directory depending on how
                it was created.

        Raises:
            RepositoryResourceNotFoundError: If no asset with the given ID exists.
        """
        asset = self._repository_service.get_resource_by_resource_id(
            resource_id=resource_id
        )
        self._logger.debug("Retrieved asset: {!r}", asset)
        return Asset(resource=asset, user_accounts_service=self._user_accounts_service)
