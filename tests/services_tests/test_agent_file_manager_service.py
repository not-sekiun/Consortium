import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import consortium.server.server_singletons as _ss
from consortium.server.services.agent_file_manager_service import (
    AgentFileManagerService,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.agent_id = uuid.uuid4()
    return agent


@pytest.fixture
def mock_assets_service():
    return MagicMock()


@pytest.fixture
def mock_artifacts_service():
    return MagicMock()


@pytest.fixture
def service(mock_agent, mock_assets_service, mock_artifacts_service):
    with (
        patch.object(_ss, "assets_service", mock_assets_service),
        patch.object(_ss, "artifacts_service", mock_artifacts_service),
    ):
        svc = AgentFileManagerService(agent=mock_agent)
    return svc, mock_assets_service, mock_artifacts_service


def test_get_all_assets_delegates(service):
    svc, assets, _ = service
    expected = [MagicMock()]
    assets.get_all_assets.return_value = expected
    result = svc.get_all_assets()
    assert result == expected
    assets.get_all_assets.assert_called_once()


def test_get_asset_by_asset_id_delegates(service):
    svc, assets, _ = service
    asset_id = uuid.uuid4()
    expected = MagicMock()
    assets.get_asset_by_asset_id.return_value = expected
    result = svc.get_asset_by_asset_id(asset_id=asset_id)
    assert result == expected
    assets.get_asset_by_asset_id.assert_called_once_with(asset_id=asset_id)


def test_get_all_artifacts_delegates(service):
    svc, _, artifacts = service
    expected = [MagicMock()]
    artifacts.get_all_artifacts.return_value = expected
    result = svc.get_all_artifacts()
    assert result == expected
    artifacts.get_all_artifacts.assert_called_once()


def test_get_artifact_by_artifact_id_delegates(service):
    svc, _, artifacts = service
    artifact_id = uuid.uuid4()
    expected = MagicMock()
    artifacts.get_artifact_by_artifact_id.return_value = expected
    result = svc.get_artifact_by_artifact_id(artifact_id=artifact_id)
    assert result == expected
    artifacts.get_artifact_by_artifact_id.assert_called_once_with(
        artifact_id=artifact_id
    )


def test_read_asset_by_asset_id_delegates_to_asset_read(service):
    svc, assets, _ = service
    asset_id = uuid.uuid4()
    asset = MagicMock()
    asset.is_directory = False
    asset.read.return_value = b"asset content"
    assets.get_asset_by_asset_id.return_value = asset

    result = svc.read_asset_by_asset_id(asset_id=asset_id, binary=True, chunk_size=1024)

    assert result == b"asset content"
    assets.get_asset_by_asset_id.assert_called_once_with(asset_id=asset_id)
    asset.read.assert_called_once_with(binary=True, encoding="utf-8", chunk_size=1024)


def test_read_asset_by_asset_id_defaults_to_text_full_read(service):
    svc, assets, _ = service
    asset_id = uuid.uuid4()
    asset = MagicMock()
    asset.is_directory = False
    asset.read.return_value = "asset content"
    assets.get_asset_by_asset_id.return_value = asset

    result = svc.read_asset_by_asset_id(asset_id=asset_id)

    assert result == "asset content"
    asset.read.assert_called_once_with(binary=False, encoding="utf-8", chunk_size=None)


def test_read_asset_by_asset_id_raises_on_directory(service):
    svc, assets, _ = service
    asset = MagicMock()
    asset.is_directory = True
    assets.get_asset_by_asset_id.return_value = asset

    with pytest.raises(IsADirectoryError):
        svc.read_asset_by_asset_id(asset_id="some_id")

    asset.read.assert_not_called()


async def test_create_artifact_file_attributes_owning_agent(service, mock_agent):
    svc, _, artifacts = service
    expected = MagicMock()
    artifacts.create_artifact_file = AsyncMock(return_value=expected)

    result = await svc.create_artifact_file(
        content=b"bytes", name="report", description="a report"
    )

    assert result == expected
    artifacts.create_artifact_file.assert_awaited_once_with(
        content=b"bytes",
        name="report",
        description="a report",
        agent_id=mock_agent.agent_id,
    )


async def test_add_artifact_file_attributes_owning_agent(service, mock_agent):
    svc, _, artifacts = service
    expected = MagicMock()
    artifacts.add_artifact_file = AsyncMock(return_value=expected)

    result = await svc.add_artifact_file(path="/tmp/out.bin", copy=True)

    assert result == expected
    artifacts.add_artifact_file.assert_awaited_once_with(
        path="/tmp/out.bin",
        name=None,
        description="",
        copy=True,
        agent_id=mock_agent.agent_id,
    )


async def test_create_artifact_directory_attributes_owning_agent(service, mock_agent):
    svc, _, artifacts = service
    expected = MagicMock()
    artifacts.create_artifact_directory = AsyncMock(return_value=expected)

    result = await svc.create_artifact_directory(
        content=b"archive", archive_file_format="zip", name="bundle"
    )

    assert result == expected
    artifacts.create_artifact_directory.assert_awaited_once_with(
        content=b"archive",
        archive_file_format="zip",
        name="bundle",
        description="",
        agent_id=mock_agent.agent_id,
    )


async def test_add_artifact_directory_attributes_owning_agent(service, mock_agent):
    svc, _, artifacts = service
    expected = MagicMock()
    artifacts.add_artifact_directory = AsyncMock(return_value=expected)

    result = await svc.add_artifact_directory(path="/tmp/outdir")

    assert result == expected
    artifacts.add_artifact_directory.assert_awaited_once_with(
        path="/tmp/outdir",
        name=None,
        description="",
        copy=False,
        agent_id=mock_agent.agent_id,
    )
