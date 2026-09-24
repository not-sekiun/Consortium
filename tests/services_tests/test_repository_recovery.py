import json
import pathlib
import shutil
import threading
from functools import partial
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from consortium.server.exceptions.object_exceptions.repository_object_exceptions import (
    RepositoryResourceFileSystemError,
)
from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    RepositoryMetadataFileEncodingError,
    RepositoryMetadataFileJSONError,
    RepositoryMetadataFileResourceDataSchemaError,
    RepositoryMetadataFileSchemaError,
    RepositoryMetadataFileSystemError,
    ResourceAlreadyExistsError,
    ResourceIDReservationNotFoundError,
    ResourceNotFoundError,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)
from consortium.server.services import repository_service as repository_module
from consortium.server.services.repository_service import RepositoryService


@pytest.fixture
def service(tmp_path):
    directory = tmp_path / "repo"
    directory.mkdir()
    return RepositoryService(directory)


def _fail_write(*args, **kwargs):
    raise OSError("injected metadata write failure")


def _read_metadata(service):
    return json.loads(
        service._repository_metadata_file_path.read_text(encoding="utf-8")
    )


def _concurrently(*operations):
    barrier = threading.Barrier(len(operations), timeout=5)
    results = [None] * len(operations)

    def run(index, operation):
        try:
            barrier.wait()
            results[index] = operation()
        except Exception as exc:
            results[index] = exc

    threads = [
        threading.Thread(target=run, args=(index, operation), daemon=True)
        for index, operation in enumerate(operations)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
    assert not any(thread.is_alive() for thread in threads), "Repository deadlock"
    return results


def test_concurrent_creates_and_public_save_preserve_every_record(service, monkeypatch):
    write = repository_module.atomic_write_bytes

    def write_while_locked(path, data):
        assert not service._lock.acquire(blocking=False)
        return write(path, data)

    monkeypatch.setattr(repository_module, "atomic_write_bytes", write_while_locked)
    first, second, saved = _concurrently(
        partial(service.create_file, content="first"),
        partial(service.create_directory, name="second"),
        service.save_repository_metadata,
    )
    assert isinstance(first, RepositoryFile)
    assert isinstance(second, RepositoryDirectory)
    assert saved is None
    assert set(_read_metadata(service)) == {
        str(first.resource_id),
        str(second.resource_id),
    }


def test_concurrent_create_and_delete_keep_index_consistent(service):
    old = service.create_file(content="old")
    created, deleted = _concurrently(
        partial(service.create_file, content="new"),
        partial(service.delete_resource_by_resource_id, old.resource_id),
    )
    assert isinstance(created, RepositoryFile)
    assert deleted is None
    assert not old.path.exists()
    assert set(_read_metadata(service)) == {str(created.resource_id)}
    assert service.get_all_resources() == [created]


def test_concurrent_deletes_return_one_success_and_one_not_found(service):
    resource = service.create_file(content="old")
    delete = partial(service.delete_resource_by_resource_id, resource.resource_id)
    results = _concurrently(delete, delete)
    assert results.count(None) == 1
    assert sum(isinstance(result, ResourceNotFoundError) for result in results) == 1
    assert _read_metadata(service) == {}


def test_concurrent_update_and_delete_do_not_reintroduce_resource(service):
    resource = service.create_file(content="old")
    updated, deleted = _concurrently(
        partial(
            service.update_resource_by_resource_id, resource.resource_id, name="new"
        ),
        partial(service.delete_resource_by_resource_id, resource.resource_id),
    )
    assert updated is resource or isinstance(updated, ResourceNotFoundError)
    assert deleted is None
    assert service.get_all_resources() == []
    assert _read_metadata(service) == {}


def test_reservation_can_be_consumed_only_once(service):
    reserved = service.reserve_resource_id()
    create = partial(service.create_file, content="x", resource_id=reserved)
    results = _concurrently(create, create)
    assert sum(isinstance(result, RepositoryFile) for result in results) == 1
    assert (
        sum(
            isinstance(result, ResourceIDReservationNotFoundError) for result in results
        )
        == 1
    )
    assert str(reserved) not in service._reserved_resource_ids


def test_lock_covers_placement_and_directory_serialization(service, monkeypatch):
    create = RepositoryDirectory.create
    serialize = RepositoryDirectory.to_json

    def create_while_locked(**kwargs):
        assert not service._lock.acquire(blocking=False)
        return create(**kwargs)

    def serialize_while_locked(resource, *args, **kwargs):
        assert not service._lock.acquire(blocking=False)
        return serialize(resource, *args, **kwargs)

    monkeypatch.setattr(RepositoryDirectory, "create", create_while_locked)
    monkeypatch.setattr(RepositoryDirectory, "to_json", serialize_while_locked)
    service.create_directory()
    service.save_repository_metadata()


@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("reserved", [False, True])
def test_failed_create_restores_memory_and_reservation(
    service, monkeypatch, directory, reserved
):
    survivor = service.create_file(content="survivor")
    resource_id = service.reserve_resource_id() if reserved else None
    create = service.create_directory if directory else service.create_file
    kwargs = {} if directory else {"content": "new"}
    with monkeypatch.context() as patch:
        patch.setattr(repository_module, "atomic_write_bytes", _fail_write)
        with pytest.raises(RepositoryMetadataFileSystemError):
            create(resource_id=resource_id, **kwargs)

    assert service.get_all_resources() == [survivor]
    assert service._reserved_resource_ids == ({str(resource_id)} if reserved else set())
    assert set(_read_metadata(service)) == {str(survivor.resource_id)}
    assert set(service.repository_directory_path.iterdir()) == {
        survivor.path,
        service._repository_metadata_file_path,
    }
    if reserved:
        created = create(resource_id=resource_id, **kwargs)
        assert str(created.resource_id) == str(resource_id)


@pytest.mark.parametrize("directory", [False, True])
def test_failed_placement_restores_reservation(service, tmp_path, directory):
    reserved = service.reserve_resource_id()
    add = service.add_directory if directory else service.add_file
    with pytest.raises(RepositoryResourceFileSystemError):
        add(path=tmp_path / "missing", resource_id=reserved)
    assert service._reserved_resource_ids == {str(reserved)}
    assert service.get_all_resources() == []


def test_failed_cleanup_keeps_orphan_out_of_index_and_survivors_loadable(
    service, monkeypatch
):
    survivor = service.create_file(content="survivor")
    reserved = service.reserve_resource_id()
    service._logger = MagicMock()

    def fail_cleanup(resource):
        assert not service._lock.acquire(blocking=False)
        raise OSError("injected cleanup failure")

    with monkeypatch.context() as patch:
        patch.setattr(repository_module, "atomic_write_bytes", _fail_write)
        patch.setattr(RepositoryFile, "delete", fail_cleanup)
        with pytest.raises(RepositoryMetadataFileSystemError):
            service.create_file(content="orphan", resource_id=reserved)

    orphan = service.repository_directory_path / str(reserved)
    assert orphan.read_text() == "orphan"
    assert service.get_all_resources() == [survivor]
    service._logger.exception.assert_called_once()
    reloaded = RepositoryService(service.repository_directory_path)
    reloaded.load_repository_metadata()
    assert len(reloaded.get_all_resources()) == 1
    assert reloaded.get_resource_by_resource_id(survivor.resource_id).path.exists()
    assert orphan.exists()


def _source(tmp_path, directory):
    source = tmp_path / "source"
    if directory:
        source.mkdir()
        (source / "content").write_bytes(b"original")
    else:
        source.write_bytes(b"original")
    return source


def _contents(path, directory):
    return (path / "content" if directory else path).read_bytes()


@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("copy", [False, True])
def test_failed_ingest_restores_source_and_reservation(
    service, tmp_path, monkeypatch, directory, copy
):
    service.save_repository_metadata()
    source = _source(tmp_path, directory)
    reserved = service.reserve_resource_id()
    add = service.add_directory if directory else service.add_file
    with monkeypatch.context() as patch:
        patch.setattr(repository_module, "atomic_write_bytes", _fail_write)
        with pytest.raises(RepositoryMetadataFileSystemError):
            add(path=source, resource_id=reserved, copy=copy)

    assert _contents(source, directory) == b"original"
    assert not (service.repository_directory_path / str(reserved)).exists()
    assert service.get_all_resources() == []
    assert service._reserved_resource_ids == {str(reserved)}
    service.load_repository_metadata()
    assert service.get_all_resources() == []


@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("failure", ["move_back", "occupied_source"])
def test_failed_move_back_preserves_bytes_and_logs_both_paths(
    service, tmp_path, monkeypatch, directory, failure
):
    source = _source(tmp_path, directory)
    reserved = service.reserve_resource_id()
    destination = service.repository_directory_path / str(reserved)
    service._logger = MagicMock()
    move = shutil.move

    def fail_move_back(src, dst, *args, **kwargs):
        if pathlib.Path(src) == destination:
            raise OSError("injected move-back failure")
        return move(src, dst, *args, **kwargs)

    def fail_save(*args, **kwargs):
        if failure == "occupied_source":
            source.write_bytes(b"replacement")
        _fail_write()

    with monkeypatch.context() as patch:
        patch.setattr(repository_module, "atomic_write_bytes", fail_save)
        if failure == "move_back":
            patch.setattr(shutil, "move", fail_move_back)
        add = service.add_directory if directory else service.add_file
        with pytest.raises(RepositoryMetadataFileSystemError):
            add(path=source, resource_id=reserved)

    assert _contents(destination, directory) == b"original"
    assert service.get_all_resources() == []
    assert service._reserved_resource_ids == {str(reserved)}
    log_args = service._logger.exception.call_args.args
    assert destination in log_args and source in log_args
    if failure == "occupied_source":
        assert source.read_bytes() == b"replacement"
    else:
        assert not source.exists()
    with pytest.raises(ResourceAlreadyExistsError):
        service.create_file(content="overwrite", resource_id=reserved)
    assert _contents(destination, directory) == b"original"


@pytest.mark.parametrize("directory", [False, True])
def test_move_back_also_handles_failure_after_placement_before_return(
    service, tmp_path, monkeypatch, directory
):
    source = _source(tmp_path, directory)
    resource_type = RepositoryDirectory if directory else RepositoryFile
    place = resource_type.from_existing_path

    def place_then_fail(**kwargs):
        place(**kwargs)
        raise RuntimeError("injected post-placement failure")

    monkeypatch.setattr(resource_type, "from_existing_path", place_then_fail)
    add = service.add_directory if directory else service.add_file
    with pytest.raises(RuntimeError, match="post-placement"):
        add(path=source)
    assert _contents(source, directory) == b"original"
    assert service.get_all_resources() == []
    assert list(service.repository_directory_path.iterdir()) == []


@pytest.mark.parametrize("failure", ["write", "serialization"])
def test_failed_update_restores_live_fields_and_next_save(
    service, monkeypatch, failure
):
    old_data = {"nested": {"value": "old"}}
    resource = service.create_file(
        content="x", name="old", description="old description", data=old_data
    )
    with monkeypatch.context() as patch:
        if failure == "write":
            patch.setattr(repository_module, "atomic_write_bytes", _fail_write)
        new_data = (
            {"value": object()} if failure == "serialization" else {"value": "new"}
        )
        expected = (
            TypeError
            if failure == "serialization"
            else RepositoryMetadataFileSystemError
        )
        with pytest.raises(expected):
            service.update_resource_by_resource_id(
                resource.resource_id, name="new", description="new", data=new_data
            )

    assert service.get_resource_by_resource_id(resource.resource_id) is resource
    assert (resource.name, resource.description) == ("old", "old description")
    assert resource.data is old_data
    service.save_repository_metadata()
    assert _read_metadata(service)[str(resource.resource_id)]["data"] == old_data
    assert _read_metadata(service)[str(resource.resource_id)]["name"] == "old"


def test_failed_delete_save_is_reconciled_on_next_load(service, monkeypatch):
    missing = service.create_directory()
    survivor = service.create_file(content="survivor")
    with monkeypatch.context() as patch:
        patch.setattr(repository_module, "atomic_write_bytes", _fail_write)
        with pytest.raises(RepositoryMetadataFileSystemError):
            service.delete_resource_by_resource_id(missing.resource_id)
    assert service.get_all_resources() == [survivor]
    assert str(missing.resource_id) in _read_metadata(service)
    reloaded = RepositoryService(service.repository_directory_path)
    reloaded.load_repository_metadata()
    assert set(_read_metadata(reloaded)) == {str(survivor.resource_id)}
    restored = reloaded.get_resource_by_resource_id(survivor.resource_id)
    assert restored.path.read_text() == "survivor"


def test_reconcile_save_failure_keeps_survivors_and_retries(service, monkeypatch):
    missing = service.create_file(content="gone")
    survivor = service.create_file(content="survivor")
    missing.path.unlink()
    reloaded = RepositoryService(service.repository_directory_path)
    reloaded._logger = MagicMock()
    with monkeypatch.context() as patch:
        patch.setattr(repository_module, "atomic_write_bytes", _fail_write)
        reloaded.load_repository_metadata()
    assert len(reloaded.get_all_resources()) == 1
    assert reloaded.get_resource_by_resource_id(survivor.resource_id).path.exists()
    assert str(missing.resource_id) in _read_metadata(reloaded)
    reloaded._logger.warning.assert_called_once()
    reloaded._logger.exception.assert_called_once()
    reloaded.save_repository_metadata()
    assert set(_read_metadata(reloaded)) == {str(survivor.resource_id)}


@pytest.mark.parametrize("absent", [False, True])
def test_repeated_load_replaces_previous_index(service, absent):
    old = service.create_file(content="old")
    if absent:
        service._repository_metadata_file_path.unlink()
    else:
        service._repository_metadata_file_path.write_text("{}", encoding="utf-8")
    service.load_repository_metadata()
    assert service.get_all_resources() == []
    assert old.path.exists()
    assert _read_metadata(service) == {}


@pytest.mark.parametrize(
    ("content", "error"),
    [
        (b"\xff", RepositoryMetadataFileEncodingError),
        (b"not json", RepositoryMetadataFileJSONError),
        (b'{"invalid": {}}', RepositoryMetadataFileSchemaError),
    ],
)
def test_corrupt_load_preserves_previous_live_index(service, content, error):
    resource = service.create_file(content="old")
    service._repository_metadata_file_path.write_bytes(content)
    with pytest.raises(error):
        service.load_repository_metadata()
    assert service.get_all_resources() == [resource]
    assert service._repository_metadata_file_path.read_bytes() == content


def test_missing_record_with_invalid_data_still_fails_validation(service):
    class DataModel(BaseModel):
        required_value: int

    resource = service.create_file(content="old")
    resource.path.unlink()
    service._data_model = DataModel
    metadata = service._repository_metadata_file_path.read_bytes()
    with pytest.raises(RepositoryMetadataFileResourceDataSchemaError):
        service.load_repository_metadata()
    assert service.get_all_resources() == [resource]
    assert service._repository_metadata_file_path.read_bytes() == metadata


def test_unreadable_resource_is_not_reconciled_as_missing(service, monkeypatch):
    resource = service.create_file(content="old")
    stat = pathlib.Path.stat
    metadata = service._repository_metadata_file_path.read_bytes()

    def deny_resource_stat(path, *args, **kwargs):
        if path == resource.path:
            raise PermissionError("injected stat failure")
        return stat(path, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "stat", deny_resource_stat)
    with pytest.raises(RepositoryMetadataFileSystemError):
        service.load_repository_metadata()
    assert service.get_all_resources() == [resource]
    assert service._repository_metadata_file_path.read_bytes() == metadata
