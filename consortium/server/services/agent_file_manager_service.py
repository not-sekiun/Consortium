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
        return self._assets_service.get_all_resources()

    def get_asset_by_asset_id(
        self,
        asset_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        return self._assets_service.get_resource_by_resource_id(
            resource_id=asset_id,
        )

    def get_all_artifacts(self) -> list[RepositoryFile | RepositoryDirectory]:
        return self._artifacts_service.get_all_resources()

    def get_artifact_by_artifact_id(
        self,
        artifact_id: str | uuid.UUID,
    ) -> RepositoryFile | RepositoryDirectory:
        return self._artifacts_service.get_resource_by_resource_id(
            resource_id=artifact_id,
        )

    def read_asset_by_asset_id(self, asset_id: str) -> bytes:
        raise NotImplementedError
        # asset = self.get_asset_by_asset_id(asset_id)
        # return asset.read()

    def write_artifact(self, data: bytes) -> None:
        if not self._agent_artifacts_folder:
            self._agent_artifacts_folder = self._artifacts_service.create_directory(
                name=str(self._agent.agent_id),
                parent_directory_id=None,
            )

        raise NotImplementedError
        # artifact = self.get_artifact_by_artifact_id(artifact_id)
        # artifact.write(data)
