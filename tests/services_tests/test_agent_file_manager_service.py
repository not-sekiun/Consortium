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


def test_read_asset_raises_not_implemented(service):
    svc, _, _ = service
    with pytest.raises(NotImplementedError):
        svc.read_asset_by_asset_id(asset_id="some_id")


async def test_write_artifact_creates_directory_then_raises(service, mock_agent):
    svc, _, artifacts = service
    mock_dir = MagicMock()
    artifacts.create_directory = AsyncMock(return_value=mock_dir)

    with pytest.raises(NotImplementedError):
        await svc.write_artifact(data=b"some bytes")

    artifacts.create_directory.assert_called_once_with(
        name=str(mock_agent.agent_id),
        parent_directory_id=None,
    )
    assert svc._agent_artifacts_folder == mock_dir


async def test_write_artifact_skips_create_on_second_call(service, mock_agent):
    svc, _, artifacts = service
    artifacts.create_directory = AsyncMock(return_value=MagicMock())

    # First call: directory is created, then NotImplementedError
    with pytest.raises(NotImplementedError):
        await svc.write_artifact(data=b"first")

    # Second call: directory already set, create_directory NOT called again
    with pytest.raises(NotImplementedError):
        await svc.write_artifact(data=b"second")

    artifacts.create_directory.assert_called_once()
