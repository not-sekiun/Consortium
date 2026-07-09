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
            A list of all asset resources. Empty if none have been uploaded.
        """
        return self._assets_service.get_all_assets()

    def get_asset_by_asset_id(
        self,
        asset_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
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

    def get_all_artifacts(self) -> list[RepositoryFile | RepositoryDirectory]:
        """Returns all artifact resources produced by agents.

        Returns:
            A list of all artifact resources. Empty if none have been created.
        """
        return self._artifacts_service.get_all_artifacts()

    def get_artifact_by_artifact_id(
        self,
        artifact_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
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

    def read_asset_by_asset_id(self, asset_id: str) -> bytes:
        """Reads the raw bytes of an asset resource by its ID.

        Args:
            asset_id: The ID of the asset to read.

        Returns:
            The raw byte content of the asset.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError
        # asset = self.get_asset_by_asset_id(asset_id)
        # return asset.read()

    async def write_artifact(self, data: bytes) -> None:
        """Writes raw bytes as a new artifact in the agent's artifact directory.

        Args:
            data: The raw bytes to write as the artifact.

        Returns:
            Nothing.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        if not self._agent_artifacts_folder:
            # The agent file manager service always attributes artifacts it creates to
            # its owning agent by threading the agent ID through to the artifacts service,
            # which resolves it into a stored agent reference.
            self._agent_artifacts_folder = (
                await self._artifacts_service.create_asset_directory(
                    name=str(self._agent.agent_id),
                    parent_directory_id=None,
                    agent_id=self._agent.agent_id,
                )
            )

        raise NotImplementedError
        # artifact = self.get_artifact_by_artifact_id(artifact_id)
        # artifact.write(data)
