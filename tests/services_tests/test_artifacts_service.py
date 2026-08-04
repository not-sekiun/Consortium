import pathlib
import shutil
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from consortium.server.exceptions.object_exceptions.repository_object_exceptions import (
    RepositoryResourceFileSystemError,
)
from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    RepositoryMetadataFileSystemError,
    ResourceNotFoundError,
)
from consortium.server.services.agents_service import AgentsService
from consortium.server.services.artifacts_service import ArtifactsService
from consortium.server.services.events_service import EventsService
from consortium.server.services.repository_service import RepositoryService

pytestmark = pytest.mark.anyio


# Package-scoped so a single root directory is registered with pytest's tmp path
# factory (instead of one per test), and explicitly removed once the package's tests
# finish rather than relying on pytest's default retention of the last few tmp path
# runs. Each test still gets its own isolated subdirectory below.
@pytest.fixture(scope="package")
def artifacts_repo_root(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[pathlib.Path]:
    d = tmp_path_factory.mktemp("artifacts_repo_root")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def repo_dir(artifacts_repo_root: pathlib.Path) -> pathlib.Path:
    d = artifacts_repo_root / uuid.uuid4().hex
    d.mkdir()
    return d


@pytest.fixture
def repo_service(repo_dir: pathlib.Path) -> RepositoryService:
    return RepositoryService(repository_directory_path=repo_dir)


@pytest.fixture
def events_service() -> MagicMock:
    mock = MagicMock(spec=EventsService)
    mock.trigger_event = MagicMock(return_value=MagicMock())
    return mock


@pytest.fixture
def agents_service() -> MagicMock:
    return MagicMock(spec=AgentsService)


@pytest.fixture
def service(
    events_service: MagicMock,
    repo_service: RepositoryService,
    agents_service: MagicMock,
) -> ArtifactsService:
    return ArtifactsService(
        events_service=events_service,
        repository_service=repo_service,
        agents_service=agents_service,
    )


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_repr(service: ArtifactsService):
    assert "ArtifactsService" in repr(service)


# ---------------------------------------------------------------------------
# load_repository_metadata / save_repository_metadata
# ---------------------------------------------------------------------------


def test_load_repository_metadata(service: ArtifactsService, repo_dir: pathlib.Path):
    service.load_repository_metadata()
    assert (repo_dir / ".repository.json").exists()


async def test_save_repository_metadata(
    service: ArtifactsService, repo_dir: pathlib.Path
):
    with patch("asyncio.create_task"):
        await service.create_artifact_file(content="x", name="x.txt")
    service.save_repository_metadata()
    import json

    data = json.loads((repo_dir / ".repository.json").read_text())
    assert len(data) == 1


# ---------------------------------------------------------------------------
# reserve_resource_id
# ---------------------------------------------------------------------------


def test_reserve_resource_id_returns_uuid(service: ArtifactsService):
    aid = service.reserve_resource_id()
    assert isinstance(aid, uuid.UUID)


# ---------------------------------------------------------------------------
# create_file
# ---------------------------------------------------------------------------


async def test_create_file_returns_repository_file(service: ArtifactsService):
    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_file(content="hello", name="hello.txt")
    assert artifact.resource_id is not None
    assert artifact.name == "hello.txt"


async def test_create_file_fires_artifact_created_event(
    service: ArtifactsService, events_service: MagicMock
):
    with patch("asyncio.create_task") as mock_task:
        await service.create_artifact_file(content="data")
    assert mock_task.called


async def test_create_file_with_reserved_id(service: ArtifactsService):
    aid = service.reserve_resource_id()
    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_file(
            content="reserved", resource_id=aid
        )
    assert str(artifact.resource_id) == str(aid)


# ---------------------------------------------------------------------------
# agent attribution
# ---------------------------------------------------------------------------


async def test_create_file_without_agent_id_stores_null_reference(
    service: ArtifactsService,
    agents_service: MagicMock,
):
    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_file(content="anon", name="anon.txt")
    assert artifact.data == {"agent": None}
    agents_service.get_agent_by_agent_id.assert_not_called()


async def test_create_file_with_agent_id_stores_reference(
    service: ArtifactsService,
    agents_service: MagicMock,
):
    agent_id = uuid.uuid4()
    # `name` is a reserved MagicMock constructor kwarg (it labels the mock rather than
    # setting a `.name` attribute), so it must be assigned after construction to be read
    # back as the plain string `PersistentAgentReferenceModel` expects.
    mock_agent = MagicMock(agent_id=agent_id)
    mock_agent.name = "agent-name"
    mock_agent.agent_type.name = "test_agent_type"
    agents_service.get_agent_by_agent_id.return_value = mock_agent

    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_file(
            content="owned",
            name="owned.txt",
            agent_id=agent_id,
        )
    assert artifact.data == {
        "agent": {
            "agent_id": str(agent_id),
            "name": "agent-name",
            "agent_type": "test_agent_type",
        },
    }
    agents_service.get_agent_by_agent_id.assert_called_once_with(agent_id=agent_id)


# ---------------------------------------------------------------------------
# add_file
# ---------------------------------------------------------------------------


async def test_add_file_moves_source(service: ArtifactsService, tmp_path: pathlib.Path):
    src = tmp_path / "src.txt"
    src.write_text("content")
    with patch("asyncio.create_task"):
        artifact = await service.add_artifact_file(path=src)
    assert not src.exists()
    assert artifact.resource_id is not None


async def test_add_file_copy_mode(service: ArtifactsService, tmp_path: pathlib.Path):
    src = tmp_path / "src.txt"
    src.write_text("content")
    with patch("asyncio.create_task"):
        await service.add_artifact_file(path=src, copy=True)
    assert src.exists()


# ---------------------------------------------------------------------------
# create_directory
# ---------------------------------------------------------------------------


async def test_create_directory_creates_dir(
    service: ArtifactsService, repo_dir: pathlib.Path
):
    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_directory(name="mydir")
    assert (repo_dir / str(artifact.resource_id)).is_dir()


async def test_create_directory_fires_event(service: ArtifactsService):
    with patch("asyncio.create_task") as mock_task:
        await service.create_artifact_directory(name="d")
    assert mock_task.called


# ---------------------------------------------------------------------------
# add_directory
# ---------------------------------------------------------------------------


async def test_add_directory_moves_source(
    service: ArtifactsService, tmp_path: pathlib.Path
):
    src = tmp_path / "srcdir"
    src.mkdir()
    with patch("asyncio.create_task"):
        artifact = await service.add_artifact_directory(path=src)
    assert not src.exists()
    assert artifact.resource_id is not None


async def test_add_directory_copy_mode(
    service: ArtifactsService, tmp_path: pathlib.Path
):
    src = tmp_path / "srcdir2"
    src.mkdir()
    with patch("asyncio.create_task"):
        await service.add_artifact_directory(path=src, copy=True)
    assert src.exists()


# ---------------------------------------------------------------------------
# delete_artifact_by_resource_id
# ---------------------------------------------------------------------------


async def test_delete_artifact_removes_resource(service: ArtifactsService):
    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_file(content="bye", name="bye.txt")
    resource_id = str(artifact.resource_id)
    with patch("asyncio.create_task"):
        await service.delete_artifact_by_resource_id(resource_id=resource_id)
    assert service.get_all_artifacts() == []


async def test_delete_artifact_fires_deleted_event(service: ArtifactsService):
    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_file(content="bye", name="bye.txt")
    resource_id = str(artifact.resource_id)
    with patch("asyncio.create_task") as mock_task:
        await service.delete_artifact_by_resource_id(resource_id=resource_id)
    assert mock_task.called


async def test_delete_artifact_not_found_raises(service: ArtifactsService):
    with pytest.raises(ResourceNotFoundError):
        with patch("asyncio.create_task"):
            await service.delete_artifact_by_resource_id(resource_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# get_all_artifacts
# ---------------------------------------------------------------------------


def test_get_all_artifacts_empty(service: ArtifactsService):
    assert service.get_all_artifacts() == []


async def test_get_all_artifacts_returns_all(service: ArtifactsService):
    with patch("asyncio.create_task"):
        await service.create_artifact_file(content="a", name="a.txt")
        await service.create_artifact_file(content="b", name="b.txt")
    assert len(service.get_all_artifacts()) == 2


# ---------------------------------------------------------------------------
# get_artifact_by_resource_id
# ---------------------------------------------------------------------------


async def test_get_artifact_by_resource_id_success(service: ArtifactsService):
    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_file(
            content="find me", name="find.txt"
        )
    found = service.get_artifact_by_resource_id(resource_id=str(artifact.resource_id))
    assert str(found.resource_id) == str(artifact.resource_id)


def test_get_artifact_by_resource_id_not_found_raises(service: ArtifactsService):
    with pytest.raises(ResourceNotFoundError):
        service.get_artifact_by_resource_id(resource_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# documented filesystem failures actually propagate
# ---------------------------------------------------------------------------
# These pin the `Raises:` contracts to real behaviour. The errors always propagated; what
# regressed before was the documentation claiming they did not exist.


async def test_add_artifact_file_missing_source_raises_resource_error(
    service: ArtifactsService, tmp_path: pathlib.Path
):
    with pytest.raises(RepositoryResourceFileSystemError):
        await service.add_artifact_file(path=tmp_path / "absent.txt")


async def test_add_artifact_directory_missing_source_raises_resource_error(
    service: ArtifactsService, tmp_path: pathlib.Path
):
    with pytest.raises(RepositoryResourceFileSystemError):
        await service.add_artifact_directory(path=tmp_path / "absent_dir")


async def test_create_artifact_file_metadata_write_failure_raises_metadata_error(
    service: ArtifactsService, monkeypatch: pytest.MonkeyPatch
):
    def raise_oserror(*args, **kwargs):
        raise OSError(5, "Input/output error")

    with patch("asyncio.create_task"):
        artifact = await service.create_artifact_file(content="x", name="x.txt")

    monkeypatch.setattr(pathlib.Path, "open", raise_oserror)

    with pytest.raises(RepositoryMetadataFileSystemError):
        await service.update_artifact_by_resource_id(
            resource_id=str(artifact.resource_id), description="updated"
        )
