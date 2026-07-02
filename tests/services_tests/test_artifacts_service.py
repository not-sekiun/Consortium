import pathlib
import shutil
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions import (
    RepositoryResourceNotFoundError,
)
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
def service(
    events_service: MagicMock, repo_service: RepositoryService
) -> ArtifactsService:
    return ArtifactsService(
        events_service=events_service,
        repository_service=repo_service,
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
        await service.create_file(content="x", name="x.txt")
    service.save_repository_metadata()
    import json

    data = json.loads((repo_dir / ".repository.json").read_text())
    assert len(data) == 1


# ---------------------------------------------------------------------------
# reserve_artifact_id
# ---------------------------------------------------------------------------


def test_reserve_artifact_id_returns_uuid(service: ArtifactsService):
    aid = service.reserve_artifact_id()
    assert isinstance(aid, uuid.UUID)


# ---------------------------------------------------------------------------
# create_file
# ---------------------------------------------------------------------------


async def test_create_file_returns_repository_file(service: ArtifactsService):
    with patch("asyncio.create_task"):
        artifact = await service.create_file(content="hello", name="hello.txt")
    assert artifact.resource_id is not None
    assert artifact.name == "hello.txt"


async def test_create_file_fires_artifact_created_event(
    service: ArtifactsService, events_service: MagicMock
):
    with patch("asyncio.create_task") as mock_task:
        await service.create_file(content="data")
    assert mock_task.called


async def test_create_file_with_reserved_id(service: ArtifactsService):
    aid = service.reserve_artifact_id()
    with patch("asyncio.create_task"):
        artifact = await service.create_file(content="reserved", resource_id=aid)
    assert str(artifact.resource_id) == str(aid)


# ---------------------------------------------------------------------------
# add_file
# ---------------------------------------------------------------------------


async def test_add_file_moves_source(service: ArtifactsService, tmp_path: pathlib.Path):
    src = tmp_path / "src.txt"
    src.write_text("content")
    with patch("asyncio.create_task"):
        artifact = await service.add_file(path=src)
    assert not src.exists()
    assert artifact.resource_id is not None


async def test_add_file_copy_mode(service: ArtifactsService, tmp_path: pathlib.Path):
    src = tmp_path / "src.txt"
    src.write_text("content")
    with patch("asyncio.create_task"):
        await service.add_file(path=src, copy=True)
    assert src.exists()


# ---------------------------------------------------------------------------
# create_directory
# ---------------------------------------------------------------------------


async def test_create_directory_creates_dir(
    service: ArtifactsService, repo_dir: pathlib.Path
):
    with patch("asyncio.create_task"):
        artifact = await service.create_directory(name="mydir")
    assert (repo_dir / str(artifact.resource_id)).is_dir()


async def test_create_directory_fires_event(service: ArtifactsService):
    with patch("asyncio.create_task") as mock_task:
        await service.create_directory(name="d")
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
        artifact = await service.add_directory(path=src)
    assert not src.exists()
    assert artifact.resource_id is not None


async def test_add_directory_copy_mode(
    service: ArtifactsService, tmp_path: pathlib.Path
):
    src = tmp_path / "srcdir2"
    src.mkdir()
    with patch("asyncio.create_task"):
        await service.add_directory(path=src, copy=True)
    assert src.exists()


# ---------------------------------------------------------------------------
# delete_artifact_by_artifact_id
# ---------------------------------------------------------------------------


async def test_delete_artifact_removes_resource(service: ArtifactsService):
    with patch("asyncio.create_task"):
        artifact = await service.create_file(content="bye", name="bye.txt")
    artifact_id = str(artifact.resource_id)
    with patch("asyncio.create_task"):
        await service.delete_artifact_by_artifact_id(artifact_id=artifact_id)
    assert service.get_all_artifacts() == []


async def test_delete_artifact_fires_deleted_event(service: ArtifactsService):
    with patch("asyncio.create_task"):
        artifact = await service.create_file(content="bye", name="bye.txt")
    artifact_id = str(artifact.resource_id)
    with patch("asyncio.create_task") as mock_task:
        await service.delete_artifact_by_artifact_id(artifact_id=artifact_id)
    assert mock_task.called


async def test_delete_artifact_not_found_raises(service: ArtifactsService):
    with pytest.raises(RepositoryResourceNotFoundError):
        with patch("asyncio.create_task"):
            await service.delete_artifact_by_artifact_id(artifact_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# get_all_artifacts
# ---------------------------------------------------------------------------


def test_get_all_artifacts_empty(service: ArtifactsService):
    assert service.get_all_artifacts() == []


async def test_get_all_artifacts_returns_all(service: ArtifactsService):
    with patch("asyncio.create_task"):
        await service.create_file(content="a", name="a.txt")
        await service.create_file(content="b", name="b.txt")
    assert len(service.get_all_artifacts()) == 2


# ---------------------------------------------------------------------------
# get_artifact_by_artifact_id
# ---------------------------------------------------------------------------


async def test_get_artifact_by_artifact_id_success(service: ArtifactsService):
    with patch("asyncio.create_task"):
        artifact = await service.create_file(content="find me", name="find.txt")
    found = service.get_artifact_by_artifact_id(artifact_id=str(artifact.resource_id))
    assert str(found.resource_id) == str(artifact.resource_id)


def test_get_artifact_by_artifact_id_not_found_raises(service: ArtifactsService):
    with pytest.raises(RepositoryResourceNotFoundError):
        service.get_artifact_by_artifact_id(artifact_id=str(uuid.uuid4()))
