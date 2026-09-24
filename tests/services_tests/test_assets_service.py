import asyncio
import json
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
from consortium.server.services import repository_service as repository_module
from consortium.server.services.assets_service import AssetsService
from consortium.server.services.events_service import EventsService
from consortium.server.services.repository_service import RepositoryService
from consortium.server.services.user_accounts_service import UserAccountsService

pytestmark = pytest.mark.anyio


# Package-scoped so a single root directory is registered with pytest's tmp path
# factory (instead of one per test), and explicitly removed once the package's tests
# finish rather than relying on pytest's default retention of the last few tmp path
# runs. Each test still gets its own isolated subdirectory below.
@pytest.fixture(scope="package")
def assets_repo_root(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[pathlib.Path]:
    d = tmp_path_factory.mktemp("assets_repo_root")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def repo_dir(assets_repo_root: pathlib.Path) -> pathlib.Path:
    d = assets_repo_root / uuid.uuid4().hex
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
def user_accounts_service() -> MagicMock:
    return MagicMock(spec=UserAccountsService)


@pytest.fixture
def service(
    events_service: MagicMock,
    repo_service: RepositoryService,
    user_accounts_service: MagicMock,
) -> AssetsService:
    return AssetsService(
        events_service=events_service,
        repository_service=repo_service,
        user_accounts_service=user_accounts_service,
    )


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_repr(service: AssetsService):
    assert "AssetsService" in repr(service)


# ---------------------------------------------------------------------------
# load_repository_metadata / save_repository_metadata
# ---------------------------------------------------------------------------


def test_load_repository_metadata(service: AssetsService, repo_dir: pathlib.Path):
    service.load_repository_metadata()
    assert (repo_dir / ".repository.json").exists()


async def test_save_repository_metadata(service: AssetsService, repo_dir: pathlib.Path):
    with patch("asyncio.create_task"):
        await service.create_asset_file(content="x", name="x.txt")
    service.save_repository_metadata()
    import json

    data = json.loads((repo_dir / ".repository.json").read_text())
    assert len(data) == 1


async def test_concurrent_asset_mutations_preserve_metadata(service, repo_service):
    with patch("consortium.server.services.assets_service.run_async_background_task"):
        first, second = await asyncio.gather(
            service.create_asset_file(content="first"),
            service.create_asset_directory(name="second"),
        )
        await asyncio.gather(
            service.update_asset_by_resource_id(first.resource_id, name="updated"),
            service.delete_asset_by_resource_id(second.resource_id),
        )
    metadata = json.loads(repo_service._repository_metadata_file_path.read_text())
    assert set(metadata) == {str(first.resource_id)}
    assert metadata[str(first.resource_id)]["name"] == "updated"
    assert len(service.get_all_assets()) == 1


@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("operation", ["create", "copy", "move"])
async def test_asset_placement_failure_rolls_back_without_creation_event(
    service, repo_service, events_service, tmp_path, monkeypatch, directory, operation
):
    reserved = service.reserve_resource_id()
    shape = "directory" if directory else "file"
    kwargs = {"resource_id": reserved}
    source = tmp_path / "source"
    if operation == "create":
        method = getattr(service, f"create_asset_{shape}")
        if not directory:
            kwargs["content"] = "new"
    else:
        method = getattr(service, f"add_asset_{shape}")
        if directory:
            source.mkdir()
            (source / "content").write_text("original")
        else:
            source.write_text("original")
        kwargs.update(path=source, copy=operation == "copy")

    def fail_write(*args, **kwargs):
        raise OSError("injected write failure")

    monkeypatch.setattr(repository_module, "atomic_write_bytes", fail_write)
    with pytest.raises(RepositoryMetadataFileSystemError):
        await method(**kwargs)
    assert repo_service.get_all_resources() == []
    assert repo_service._reserved_resource_ids == {str(reserved)}
    assert not (repo_service.repository_directory_path / str(reserved)).exists()
    if operation != "create":
        assert (source / "content" if directory else source).read_text() == "original"
    events_service.trigger_event.assert_not_called()


async def test_failed_asset_update_restores_live_metadata(
    service, repo_service, events_service, monkeypatch
):
    with patch("consortium.server.services.assets_service.run_async_background_task"):
        asset = await service.create_asset_file(content="x", name="original")
    events_service.trigger_event.reset_mock()
    resource = repo_service.get_resource_by_resource_id(asset.resource_id)

    def fail_write(*args, **kwargs):
        raise OSError("injected write failure")

    monkeypatch.setattr(repository_module, "atomic_write_bytes", fail_write)
    with pytest.raises(RepositoryMetadataFileSystemError):
        await service.update_asset_by_resource_id(asset.resource_id, name="failed")
    assert resource.name == "original"
    events_service.trigger_event.assert_not_called()


# ---------------------------------------------------------------------------
# reserve_resource_id
# ---------------------------------------------------------------------------


def test_reserve_resource_id_returns_uuid(service: AssetsService):
    aid = service.reserve_resource_id()
    assert isinstance(aid, uuid.UUID)


# ---------------------------------------------------------------------------
# create_file
# ---------------------------------------------------------------------------


async def test_create_file_returns_repository_file(service: AssetsService):
    with patch("asyncio.create_task"):
        asset = await service.create_asset_file(content="hello", name="hello.txt")
    assert asset.resource_id is not None
    assert asset.name == "hello.txt"


async def test_create_file_fires_asset_created_event(service: AssetsService):
    with patch("asyncio.create_task") as mock_task:
        await service.create_asset_file(content="data")
    assert mock_task.called


async def test_create_file_with_reserved_id(service: AssetsService):
    aid = service.reserve_resource_id()
    with patch("asyncio.create_task"):
        asset = await service.create_asset_file(content="reserved", resource_id=aid)
    assert str(asset.resource_id) == str(aid)


# ---------------------------------------------------------------------------
# user account attribution
# ---------------------------------------------------------------------------


async def test_create_file_without_user_account_id_stores_null_reference(
    service: AssetsService,
    user_accounts_service: MagicMock,
):
    with patch("asyncio.create_task"):
        asset = await service.create_asset_file(content="anon", name="anon.txt")
    assert asset.data == {"user_account": None}
    user_accounts_service.get_user_account_by_user_account_id.assert_not_called()


async def test_create_file_with_user_account_id_stores_reference(
    service: AssetsService,
    user_accounts_service: MagicMock,
):
    user_account_id = uuid.uuid4()
    user_accounts_service.get_user_account_by_user_account_id.return_value = MagicMock(
        user_account_id=user_account_id,
        username="uploader",
        role="admin",
    )
    with patch("asyncio.create_task"):
        asset = await service.create_asset_file(
            content="owned",
            name="owned.txt",
            user_account_id=user_account_id,
        )
    assert asset.data == {
        "user_account": {
            "username": "uploader",
            "role": "admin",
        },
    }
    user_accounts_service.get_user_account_by_user_account_id.assert_called_once_with(
        user_account_id=user_account_id,
    )


# ---------------------------------------------------------------------------
# add_file
# ---------------------------------------------------------------------------


async def test_add_file_moves_source(service: AssetsService, tmp_path: pathlib.Path):
    src = tmp_path / "src.txt"
    src.write_text("content")
    with patch("asyncio.create_task"):
        asset = await service.add_asset_file(path=src)
    assert not src.exists()
    assert asset.resource_id is not None


async def test_add_file_copy_mode(service: AssetsService, tmp_path: pathlib.Path):
    src = tmp_path / "src.txt"
    src.write_text("content")
    with patch("asyncio.create_task"):
        await service.add_asset_file(path=src, copy=True)
    assert src.exists()


# ---------------------------------------------------------------------------
# create_directory
# ---------------------------------------------------------------------------


async def test_create_directory_creates_dir(
    service: AssetsService, repo_dir: pathlib.Path
):
    with patch("asyncio.create_task"):
        asset = await service.create_asset_directory(name="mydir")
    assert (repo_dir / str(asset.resource_id)).is_dir()


async def test_create_directory_fires_event(service: AssetsService):
    with patch("asyncio.create_task") as mock_task:
        await service.create_asset_directory()
    assert mock_task.called


# ---------------------------------------------------------------------------
# add_directory
# ---------------------------------------------------------------------------


async def test_add_directory_moves_source(
    service: AssetsService, tmp_path: pathlib.Path
):
    src = tmp_path / "srcdir"
    src.mkdir()
    with patch("asyncio.create_task"):
        asset = await service.add_asset_directory(path=src)
    assert not src.exists()
    assert asset.resource_id is not None


async def test_add_directory_copy_mode(service: AssetsService, tmp_path: pathlib.Path):
    src = tmp_path / "srcdir2"
    src.mkdir()
    with patch("asyncio.create_task"):
        await service.add_asset_directory(path=src, copy=True)
    assert src.exists()


# ---------------------------------------------------------------------------
# delete_asset_by_resource_id
# ---------------------------------------------------------------------------


async def test_delete_asset_removes_resource(service: AssetsService):
    with patch("asyncio.create_task"):
        asset = await service.create_asset_file(content="bye", name="bye.txt")
    resource_id = str(asset.resource_id)
    with patch("asyncio.create_task"):
        await service.delete_asset_by_resource_id(resource_id=resource_id)
    assert service.get_all_assets() == []


async def test_delete_asset_fires_deleted_event(service: AssetsService):
    with patch("asyncio.create_task"):
        asset = await service.create_asset_file(content="bye", name="bye.txt")
    resource_id = str(asset.resource_id)
    with patch("asyncio.create_task") as mock_task:
        await service.delete_asset_by_resource_id(resource_id=resource_id)
    assert mock_task.called


async def test_delete_asset_not_found_raises(service: AssetsService):
    with pytest.raises(ResourceNotFoundError):
        with patch("asyncio.create_task"):
            await service.delete_asset_by_resource_id(resource_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# get_all_assets
# ---------------------------------------------------------------------------


def test_get_all_assets_empty(service: AssetsService):
    assert service.get_all_assets() == []


async def test_get_all_assets_returns_all(service: AssetsService):
    with patch("asyncio.create_task"):
        await service.create_asset_file(content="a", name="a.txt")
        await service.create_asset_file(content="b", name="b.txt")
    assert len(service.get_all_assets()) == 2


# ---------------------------------------------------------------------------
# get_asset_by_resource_id
# ---------------------------------------------------------------------------


async def test_get_asset_by_resource_id_success(service: AssetsService):
    with patch("asyncio.create_task"):
        asset = await service.create_asset_file(content="find me", name="find.txt")
    found = service.get_asset_by_resource_id(resource_id=str(asset.resource_id))
    assert str(found.resource_id) == str(asset.resource_id)


def test_get_asset_by_resource_id_not_found_raises(service: AssetsService):
    with pytest.raises(ResourceNotFoundError):
        service.get_asset_by_resource_id(resource_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# documented filesystem failures actually propagate
# ---------------------------------------------------------------------------
# These pin the `Raises:` contracts to real behaviour. The errors always propagated; what
# regressed before was the documentation claiming they did not exist.


async def test_add_asset_file_missing_source_raises_resource_error(
    service: AssetsService, tmp_path: pathlib.Path
):
    with pytest.raises(RepositoryResourceFileSystemError):
        await service.add_asset_file(path=tmp_path / "absent.txt")


async def test_add_asset_directory_missing_source_raises_resource_error(
    service: AssetsService, tmp_path: pathlib.Path
):
    with pytest.raises(RepositoryResourceFileSystemError):
        await service.add_asset_directory(path=tmp_path / "absent_dir")


async def test_update_asset_metadata_write_failure_raises_metadata_error(
    service: AssetsService, monkeypatch: pytest.MonkeyPatch
):
    def raise_oserror(*args, **kwargs):
        raise OSError(5, "Input/output error")

    with patch("asyncio.create_task"):
        asset = await service.create_asset_file(content="x", name="x.txt")

    monkeypatch.setattr(pathlib.Path, "open", raise_oserror)

    with pytest.raises(RepositoryMetadataFileSystemError):
        await service.update_asset_by_resource_id(
            resource_id=str(asset.resource_id), description="updated"
        )
