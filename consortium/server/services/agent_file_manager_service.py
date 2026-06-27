import uuid
from typing import TYPE_CHECKING

from consortium.server import server_singletons as server_singletons
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent


class AgentFileManagerService:
    def __init__(self, agent: Agent):
        # Assets service consists of all uploaded files onto the server that are meant
        # to be read only by agents.
        self._agent = agent
        self._assets_service = server_singletons.assets_service
        self._artifacts_service = server_singletons.artifacts_service
        self._agent_artifacts_folder = None

    def get_all_assets(self) -> list[RepositoryFile | RepositoryDirectory]:
        """Returns all asset resources available to the agent.

        Returns:
            list[RepositoryFile | RepositoryDirectory]: A list of all asset resources.
                Empty if none have been uploaded.
        """
        return self._assets_service.get_all_resources()

    def get_asset_by_asset_id(
        self,
        asset_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        """Returns a single asset resource by its ID.

        Args:
            asset_id (str | uuid.UUID): The ID of the asset resource to retrieve.

        Returns:
            RepositoryFile | RepositoryDirectory: The requested asset resource.

        Raises:
            RepositoryResourceNotFoundError: If no asset with the given ID exists.
        """
        return self._assets_service.get_resource_by_resource_id(
            resource_id=asset_id,
        )

    def get_all_artifacts(self) -> list[RepositoryFile | RepositoryDirectory]:
        """Returns all artifact resources produced by agents.

        Returns:
            list[RepositoryFile | RepositoryDirectory]: A list of all artifact
                resources. Empty if none have been created.
        """
        return self._artifacts_service.get_all_resources()

    def get_artifact_by_artifact_id(
        self,
        artifact_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        """Returns a single artifact resource by its ID.

        Args:
            artifact_id (str | uuid.UUID): The ID of the artifact resource to retrieve.

        Returns:
            RepositoryFile | RepositoryDirectory: The requested artifact resource.

        Raises:
            RepositoryResourceNotFoundError: If no artifact with the given ID exists.
        """
        return self._artifacts_service.get_resource_by_resource_id(
            resource_id=artifact_id,
        )

    def read_asset_by_asset_id(self, asset_id: str) -> bytes:
        """Reads the raw bytes of an asset resource by its ID.

        Args:
            asset_id (str): The ID of the asset to read.

        Returns:
            bytes: The raw byte content of the asset.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError
        # asset = self.get_asset_by_asset_id(asset_id)
        # return asset.read()

    def write_artifact(self, data: bytes) -> None:
        """Writes raw bytes as a new artifact in the agent's artifact directory.

        Args:
            data (bytes): The raw bytes to write as the artifact.

        Returns:
            None

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        if not self._agent_artifacts_folder:
            self._agent_artifacts_folder = self._artifacts_service.create_directory(
                name=str(self._agent.agent_id),
                parent_directory_id=None,
            )

        raise NotImplementedError
        # artifact = self.get_artifact_by_artifact_id(artifact_id)
        # artifact.write(data)
