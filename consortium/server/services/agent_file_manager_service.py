import uuid
from typing import TYPE_CHECKING

from consortium.server import server_singletons as server_singletons

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Generator
    from typing import BinaryIO, Literal, TextIO

    from consortium.server.objects.agent_objects import Agent
    from consortium.server.objects.artifact_objects import Artifact
    from consortium.server.objects.asset_objects import Asset


class AgentFileManagerService:
    def __init__(self, agent: Agent):
        # The agent file manager service is the agent-facing facade over the shared
        # assets and artifacts services. Assets are the pool of uploaded files an agent
        # may read; artifacts are the files and directories an agent produces. Every
        # artifact written through this facade is attributed to the owning agent by
        # threading its agent ID into the artifacts service, which resolves it into a
        # stored agent reference.
        self._agent = agent
        self._assets_service = server_singletons.assets_service
        self._artifacts_service = server_singletons.artifacts_service

    def get_all_assets(self) -> list[Asset]:
        """Returns all asset resources available to the agent.

        Returns:
            A list of all asset resources. Empty if none have been uploaded.
        """
        return self._assets_service.get_all_assets()

    def get_asset_by_asset_id(
        self,
        asset_id: str | uuid.UUID,
    ) -> Asset:
        """Returns a single asset resource by its ID.

        Args:
            asset_id: The ID of the asset resource to retrieve.

        Returns:
            The requested asset resource.

        Raises:
            RepositoryResourceNotFoundError: If no asset with the given ID exists.
        """
        return self._assets_service.get_asset_by_asset_id(
            asset_id=asset_id,
        )

    def get_all_artifacts(self) -> list[Artifact]:
        """Returns all artifact resources produced by agents.

        Returns:
            A list of all artifact resources. Empty if none have been created.
        """
        return self._artifacts_service.get_all_artifacts()

    def get_artifact_by_artifact_id(
        self,
        artifact_id: str | uuid.UUID,
    ) -> Artifact:
        """Returns a single artifact resource by its ID.

        Args:
            artifact_id: The ID of the artifact resource to retrieve.

        Returns:
            The requested artifact resource.

        Raises:
            RepositoryResourceNotFoundError: If no artifact with the given ID exists.
        """
        return self._artifacts_service.get_artifact_by_artifact_id(
            artifact_id=artifact_id,
        )

    def read_asset_by_asset_id(
        self,
        asset_id: str | uuid.UUID,
        binary: bool = False,
        encoding: str = "utf-8",
        chunk_size: int | None = None,
    ) -> str | bytes | Generator[str | bytes]:
        """Reads the content of a file asset by its ID.

        Retrieves the asset and reads its content from disk. The full read spectrum of
        the underlying repository file is exposed: content can be read as text or as raw
        bytes, and either eagerly (the whole content at once) or lazily as a generator of
        chunks for streaming large assets without loading them fully into memory.

        Args:
            asset_id: The ID of the asset to read.
            binary: When `True`, the content is read as raw bytes; when `False` (default)
                it is decoded to text using `encoding`.
            encoding: The text encoding used to decode the content when `binary` is
                `False`. Ignored when `binary` is `True`.
            chunk_size: When `None` (default) the entire content is read and returned in
                one piece. When set to a positive integer, a generator is returned that
                yields the content in chunks of at most this many bytes (binary) or
                characters (text), for streaming.

        Returns:
            The asset's content: a `str` (text) or `bytes` (binary) when `chunk_size` is
                `None`, otherwise a generator yielding successive `str` or `bytes` chunks.

        Raises:
            RepositoryResourceNotFoundError: If no asset with the given ID exists.
            IsADirectoryError: If the asset is a directory, which has no readable file
                content.
            RepositoryFileDoesNotExistError: If the asset is a file but no longer exists
                on disk.
        """
        asset = self.get_asset_by_asset_id(asset_id=asset_id)
        # Directory assets have no single readable content stream; reading one as a file
        # is a caller error, so surface it explicitly rather than letting the missing
        # `read` attribute raise an opaque AttributeError.
        if asset.is_directory:
            raise IsADirectoryError(
                f"Asset '{asset_id}' is a directory and cannot be read as a file"
            )
        return asset.read(
            binary=binary,
            encoding=encoding,
            chunk_size=chunk_size,
        )

    async def create_artifact_file(
        self,
        content: str | bytes | TextIO | BinaryIO,
        name: str | None = None,
        description: str = "",
    ) -> Artifact:
        """Creates a new artifact file from in-memory or streamed content.

        The content is written to a new file in the artifacts repository and attributed
        to the owning agent.

        Args:
            content: The content to write into the new artifact file, supplied either
                directly as text/bytes or as an open text/binary stream to read from.
            name: A human-readable display name for the artifact. When `None`, the
                artifact's generated UUID is used as its name.
            description: A short human-readable description of the artifact. Defaults to
                an empty string when omitted.

        Returns:
            The newly created artifact file resource, attributed to the owning agent.
        """
        return await self._artifacts_service.create_artifact_file(
            content=content,
            name=name,
            description=description,
            agent_id=self._agent.agent_id,
        )

    async def add_artifact_file(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        copy: bool = False,
    ) -> Artifact:
        """Registers an existing file on disk as an artifact.

        No new content is written: the file at `path` is moved (or copied when
        `copy=True`) into the artifacts repository and attributed to the owning agent.

        Args:
            path: Filesystem path to the existing file to ingest as an artifact.
            name: A human-readable display name for the artifact. When `None`, the
                original filename is used.
            description: A short human-readable description of the artifact. Defaults to
                an empty string when omitted.
            copy: When `False` (default) the source file is moved into the repository,
                leaving nothing at the original path. When `True` the source file is
                copied and the original is left in place.

        Returns:
            The newly registered artifact file resource, attributed to the owning agent.
        """
        return await self._artifacts_service.add_artifact_file(
            path=path,
            name=name,
            description=description,
            copy=copy,
            agent_id=self._agent.agent_id,
        )

    async def create_artifact_directory(
        self,
        content: bytes | BinaryIO | str | pathlib.Path | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"]
        | None = None,
        name: str | None = None,
        description: str = "",
    ) -> Artifact:
        """Creates a new artifact directory, optionally populated from an archive.

        An empty directory is created in the artifacts repository, or, when `content` and
        `archive_file_format` are provided, the archive content is extracted into it. The
        directory is attributed to the owning agent.

        Args:
            content: Archive content to extract into the new directory, supplied as raw
                bytes, an open binary stream, or a path to an archive file. When `None`,
                an empty directory is created.
            archive_file_format: The archive format used to interpret `content` when
                extracting. Must be set whenever `content` is provided; ignored when
                `content` is `None`.
            name: A human-readable display name for the artifact. When `None`, the
                artifact's generated UUID is used as its name.
            description: A short human-readable description of the artifact. Defaults to
                an empty string when omitted.

        Returns:
            The newly created artifact directory resource, attributed to the owning
                agent.
        """
        return await self._artifacts_service.create_artifact_directory(
            content=content,
            archive_file_format=archive_file_format,
            name=name,
            description=description,
            agent_id=self._agent.agent_id,
        )

    async def add_artifact_directory(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        copy: bool = False,
    ) -> Artifact:
        """Registers an existing directory on disk as an artifact.

        No new directory is created: the directory at `path` is moved (or copied when
        `copy=True`) into the artifacts repository and attributed to the owning agent.

        Args:
            path: Filesystem path to the existing directory to ingest as an artifact.
            name: A human-readable display name for the artifact. When `None`, the
                original directory name is used.
            description: A short human-readable description of the artifact. Defaults to
                an empty string when omitted.
            copy: When `False` (default) the source directory is moved into the
                repository, leaving nothing at the original path. When `True` the source
                directory is copied and the original is left in place.

        Returns:
            The newly registered artifact directory resource, attributed to the owning
                agent.
        """
        return await self._artifacts_service.add_artifact_directory(
            path=path,
            name=name,
            description=description,
            copy=copy,
            agent_id=self._agent.agent_id,
        )
