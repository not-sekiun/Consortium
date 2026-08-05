import json
import pathlib
import shutil
import uuid

import pytest

from consortium.server.exceptions.object_exceptions.repository_object_exceptions import (
    RepositoryResourceFileSystemError,
)
from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    RepositoryMetadataFileEncodingError,
    RepositoryMetadataFileJSONError,
    RepositoryMetadataFileSchemaError,
    RepositoryMetadataFileSystemError,
    RepositoryMetadataFileUnsyncedError,
    ResourceIDReservationNotFoundError,
    ResourceNotFoundError,
)
from consortium.server.services.repository_service import RepositoryService

# A resource name carrying non-ASCII characters. Used to pin the explicit UTF-8 encoding
# on the metadata file: under a non-UTF-8 locale default these bytes either mojibake or
# fail to decode outright.
_NON_ASCII_NAME = "wörker.txt"


def _metadata_entry(resource_id: str, name: str, is_directory: bool = False) -> dict:
    return {
        "resource_id": resource_id,
        "name": name,
        "description": "",
        "size": None,
        "extension": "",
        "exists_on_disk": True,
        "md5_checksum": None,
        "datetime_created": "2024-01-01T00:00:00",
        "datetime_modified": "2024-01-01T00:00:00",
        "is_directory": is_directory,
        "data": {},
    }


def _raise_oserror(*args, **kwargs):
    # Stands in for the residual `OSError` family (ENOSPC, EIO) that no pre-flight check
    # can rule out.
    raise OSError(5, "Input/output error")


@pytest.fixture
def repo_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    d = tmp_path / "repo"
    d.mkdir()
    return d


@pytest.fixture
def service(repo_dir: pathlib.Path) -> RepositoryService:
    return RepositoryService(repository_directory_path=repo_dir)


# ---------------------------------------------------------------------------
# __str__ / __repr__
# ---------------------------------------------------------------------------


def test_str(service: RepositoryService):
    assert str(service) == "Repository Service"


def test_repr(service: RepositoryService):
    assert "RepositoryService" in repr(service)


# ---------------------------------------------------------------------------
# load_repository_metadata - no file yet (creates empty metadata file)
# ---------------------------------------------------------------------------


def test_load_repository_metadata_creates_metadata_file_when_absent(
    service: RepositoryService, repo_dir: pathlib.Path
):
    assert not (repo_dir / ".repository.json").exists()
    service.load_repository_metadata()
    assert (repo_dir / ".repository.json").exists()


def test_load_repository_metadata_empty_metadata_leaves_resources_empty(
    service: RepositoryService,
):
    service.load_repository_metadata()
    assert service.get_all_resources() == []


# ---------------------------------------------------------------------------
# load_repository_metadata - invalid JSON
# ---------------------------------------------------------------------------


def test_load_repository_metadata_invalid_json_raises(
    service: RepositoryService, repo_dir: pathlib.Path
):
    (repo_dir / ".repository.json").write_text("not json {{{{")
    with pytest.raises(RepositoryMetadataFileJSONError):
        service.load_repository_metadata()


# ---------------------------------------------------------------------------
# load_repository_metadata - invalid schema
# ---------------------------------------------------------------------------


def test_load_repository_metadata_invalid_schema_raises(
    service: RepositoryService, repo_dir: pathlib.Path
):
    # Write valid JSON but that doesn't match the schema (value is string not object)
    (repo_dir / ".repository.json").write_text(json.dumps({"abc123": "not an object"}))
    with pytest.raises(RepositoryMetadataFileSchemaError):
        service.load_repository_metadata()


# ---------------------------------------------------------------------------
# load_repository_metadata - unsynced resource (on-disk file missing)
# ---------------------------------------------------------------------------


def test_load_repository_metadata_unsynced_file_raises(
    service: RepositoryService, repo_dir: pathlib.Path
):
    import uuid

    resource_id = str(uuid.uuid4())
    metadata = {
        resource_id: {
            "resource_id": resource_id,
            "name": "missing_file.txt",
            "description": "",
            "size": None,
            "extension": "",
            "exists_on_disk": True,
            "md5_checksum": None,
            "datetime_created": "2024-01-01T00:00:00",
            "datetime_modified": "2024-01-01T00:00:00",
            "is_directory": False,
            "data": {},
        }
    }
    (repo_dir / ".repository.json").write_text(json.dumps(metadata))
    with pytest.raises(RepositoryMetadataFileUnsyncedError):
        service.load_repository_metadata()


# ---------------------------------------------------------------------------
# load_repository_metadata - loads valid files from metadata
# ---------------------------------------------------------------------------


def test_load_repository_metadata_loads_file_resource(
    service: RepositoryService, repo_dir: pathlib.Path
):
    # First create a file through the service so metadata is saved correctly
    f = service.create_file(content="hello", name="hello.txt")
    resource_id = str(f.resource_id)

    # Re-create the service and reload
    svc2 = RepositoryService(repository_directory_path=repo_dir)
    svc2.load_repository_metadata()
    resources = svc2.get_all_resources()
    assert len(resources) == 1
    assert str(resources[0].resource_id) == resource_id


def test_load_repository_metadata_loads_directory_resource(
    service: RepositoryService, repo_dir: pathlib.Path
):
    d = service.create_directory(name="mydir")
    resource_id = str(d.resource_id)

    svc2 = RepositoryService(repository_directory_path=repo_dir)
    svc2.load_repository_metadata()
    resources = svc2.get_all_resources()
    assert len(resources) == 1
    assert str(resources[0].resource_id) == resource_id


# ---------------------------------------------------------------------------
# reserve_resource_id
# ---------------------------------------------------------------------------


def test_reserve_resource_id_returns_uuid(service: RepositoryService):
    import uuid

    rid = service.reserve_resource_id()
    assert isinstance(rid, uuid.UUID)


def test_reserve_resource_id_is_usable_in_create_file(service: RepositoryService):
    rid = service.reserve_resource_id()
    f = service.create_file(content="data", resource_id=rid)
    assert str(f.resource_id) == str(rid)


# ---------------------------------------------------------------------------
# create_file
# ---------------------------------------------------------------------------


def test_create_file_with_auto_id(service: RepositoryService):
    f = service.create_file(content="test content", name="test.txt")
    assert f.resource_id is not None
    assert f.name == "test.txt"
    resources = service.get_all_resources()
    assert len(resources) == 1


def test_create_file_with_reserved_id(service: RepositoryService):
    rid = service.reserve_resource_id()
    f = service.create_file(content="content", name="file.txt", resource_id=rid)
    assert str(f.resource_id) == str(rid)


def test_create_file_with_unreserved_id_raises(service: RepositoryService):
    import uuid

    with pytest.raises(ResourceIDReservationNotFoundError):
        service.create_file(content="content", resource_id=uuid.uuid4())


def test_create_file_persists_metadata(
    service: RepositoryService, repo_dir: pathlib.Path
):
    service.create_file(content="persisted", name="p.txt")
    assert (repo_dir / ".repository.json").exists()
    data = json.loads((repo_dir / ".repository.json").read_text())
    assert len(data) == 1


def test_create_file_preserves_extension(
    service: RepositoryService, repo_dir: pathlib.Path
):
    f = service.create_file(content="data", name="archive.tar.gz")
    # The on-disk file should carry the extension
    assert f.path.suffix == ".gz"


def test_create_file_bytes_content(service: RepositoryService):
    f = service.create_file(content=b"\x00\x01\x02", name="binary.bin")
    assert f.resource_id is not None


# ---------------------------------------------------------------------------
# add_file
# ---------------------------------------------------------------------------


def test_add_file_moves_by_default(
    service: RepositoryService, tmp_path: pathlib.Path, repo_dir: pathlib.Path
):
    src = tmp_path / "source.txt"
    src.write_text("hello")
    f = service.add_file(path=src)
    assert not src.exists()
    assert f.path.exists()


def test_add_file_copy_leaves_original(
    service: RepositoryService, tmp_path: pathlib.Path
):
    src = tmp_path / "source.txt"
    src.write_text("hello")
    service.add_file(path=src, copy=True)
    assert src.exists()


def test_add_file_with_reserved_id(service: RepositoryService, tmp_path: pathlib.Path):
    src = tmp_path / "source.txt"
    src.write_text("hello")
    rid = service.reserve_resource_id()
    f = service.add_file(path=src, resource_id=rid)
    assert str(f.resource_id) == str(rid)


def test_add_file_with_unreserved_id_raises(
    service: RepositoryService, tmp_path: pathlib.Path
):
    import uuid

    src = tmp_path / "source.txt"
    src.write_text("hello")
    with pytest.raises(ResourceIDReservationNotFoundError):
        service.add_file(path=src, resource_id=uuid.uuid4())


def test_add_file_uses_original_name_when_name_not_provided(
    service: RepositoryService, tmp_path: pathlib.Path
):
    src = tmp_path / "myfile.dat"
    src.write_text("data")
    f = service.add_file(path=src)
    assert f.name == "myfile.dat"


def test_add_file_string_path(service: RepositoryService, tmp_path: pathlib.Path):
    src = tmp_path / "str_path.txt"
    src.write_text("hello")
    f = service.add_file(path=str(src))
    assert f.resource_id is not None


# ---------------------------------------------------------------------------
# create_directory
# ---------------------------------------------------------------------------


def test_create_directory_empty(service: RepositoryService, repo_dir: pathlib.Path):
    d = service.create_directory(name="mydir")
    assert d.resource_id is not None
    assert (repo_dir / str(d.resource_id)).is_dir()


def test_create_directory_with_reserved_id(service: RepositoryService):
    rid = service.reserve_resource_id()
    d = service.create_directory(name="reserved_dir", resource_id=rid)
    assert str(d.resource_id) == str(rid)


def test_create_directory_with_unreserved_id_raises(service: RepositoryService):
    import uuid

    with pytest.raises(ResourceIDReservationNotFoundError):
        service.create_directory(resource_id=uuid.uuid4())


def test_create_directory_persists_metadata(
    service: RepositoryService, repo_dir: pathlib.Path
):
    service.create_directory()
    data = json.loads((repo_dir / ".repository.json").read_text())
    assert len(data) == 1


# ---------------------------------------------------------------------------
# add_directory
# ---------------------------------------------------------------------------


def test_add_directory_moves_by_default(
    service: RepositoryService, tmp_path: pathlib.Path, repo_dir: pathlib.Path
):
    src = tmp_path / "mydir"
    src.mkdir()
    (src / "file.txt").write_text("hello")
    d = service.add_directory(path=src)
    assert not src.exists()
    assert d.path.is_dir()


def test_add_directory_copy_leaves_original(
    service: RepositoryService, tmp_path: pathlib.Path
):
    src = tmp_path / "mydir2"
    src.mkdir()
    service.add_directory(path=src, copy=True)
    assert src.exists()


def test_add_directory_with_reserved_id(
    service: RepositoryService, tmp_path: pathlib.Path
):
    src = tmp_path / "reserved"
    src.mkdir()
    rid = service.reserve_resource_id()
    d = service.add_directory(path=src, resource_id=rid)
    assert str(d.resource_id) == str(rid)


def test_add_directory_with_unreserved_id_raises(
    service: RepositoryService, tmp_path: pathlib.Path
):
    import uuid

    src = tmp_path / "unreserved"
    src.mkdir()
    with pytest.raises(ResourceIDReservationNotFoundError):
        service.add_directory(path=src, resource_id=uuid.uuid4())


def test_add_directory_string_path(service: RepositoryService, tmp_path: pathlib.Path):
    src = tmp_path / "strdir"
    src.mkdir()
    d = service.add_directory(path=str(src))
    assert d.resource_id is not None


# ---------------------------------------------------------------------------
# delete_resource_by_resource_id
# ---------------------------------------------------------------------------


def test_delete_file_resource(service: RepositoryService):
    f = service.create_file(content="delete me", name="del.txt")
    rid = str(f.resource_id)
    service.delete_resource_by_resource_id(resource_id=rid)
    assert service.get_all_resources() == []


def test_delete_directory_resource(service: RepositoryService):
    d = service.create_directory(name="del_dir")
    rid = str(d.resource_id)
    service.delete_resource_by_resource_id(resource_id=rid)
    assert service.get_all_resources() == []


def test_delete_resource_not_found_raises(service: RepositoryService):
    import uuid

    with pytest.raises(ResourceNotFoundError):
        service.delete_resource_by_resource_id(resource_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# get_resource_by_resource_id
# ---------------------------------------------------------------------------


def test_get_resource_by_resource_id_not_found_raises(service: RepositoryService):
    import uuid

    with pytest.raises(ResourceNotFoundError):
        service.get_resource_by_resource_id(resource_id=str(uuid.uuid4()))


def test_get_resource_by_resource_id_success(service: RepositoryService):
    f = service.create_file(content="find me", name="find.txt")
    result = service.get_resource_by_resource_id(resource_id=str(f.resource_id))
    assert str(result.resource_id) == str(f.resource_id)


# ---------------------------------------------------------------------------
# get_all_resources
# ---------------------------------------------------------------------------


def test_get_all_resources_returns_all(service: RepositoryService):
    service.create_file(content="a", name="a.txt")
    service.create_file(content="b", name="b.txt")
    service.create_directory(name="c")
    assert len(service.get_all_resources()) == 3


def test_get_all_resources_empty_on_fresh_service(service: RepositoryService):
    assert service.get_all_resources() == []


# ---------------------------------------------------------------------------
# metadata file encoding
# ---------------------------------------------------------------------------


def test_load_repository_metadata_decodes_utf8_names(
    service: RepositoryService, repo_dir: pathlib.Path
):
    # Written with `ensure_ascii=False` so the non-ASCII name lands in the file as real
    # UTF-8 bytes rather than as `\uXXXX` escapes. This is what a hand-edited or
    # externally written metadata file looks like, and it is the case that regresses if
    # the read stops pinning the encoding: under a cp1252 default these bytes decode to
    # mojibake instead of raising.
    resource_id = str(uuid.uuid4())
    resource_path = repo_dir / resource_id
    resource_path.write_text("content")
    metadata = {resource_id: _metadata_entry(resource_id, _NON_ASCII_NAME)}
    (repo_dir / ".repository.json").write_text(
        json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
    )

    service.load_repository_metadata()

    assert service.get_all_resources()[0].name == _NON_ASCII_NAME


def test_metadata_round_trips_non_ascii_names(
    service: RepositoryService, repo_dir: pathlib.Path
):
    service.create_file(content="hello", name=_NON_ASCII_NAME)

    reloaded = RepositoryService(repository_directory_path=repo_dir)
    reloaded.load_repository_metadata()

    assert reloaded.get_all_resources()[0].name == _NON_ASCII_NAME


def test_load_repository_metadata_invalid_utf8_raises_encoding_error(
    service: RepositoryService, repo_dir: pathlib.Path
):
    # A decode failure must be reported as its own condition rather than escaping as a
    # raw `UnicodeDecodeError` or being misreported as a JSON syntax error: the bytes
    # never became text, so the file was never parsed.
    (repo_dir / ".repository.json").write_bytes(b'{"\xff\xfe": {}}')

    with pytest.raises(RepositoryMetadataFileEncodingError):
        service.load_repository_metadata()


# ---------------------------------------------------------------------------
# filesystem errors: metadata vs resource
# ---------------------------------------------------------------------------


def test_save_repository_metadata_filesystem_error_is_metadata_scoped(
    service: RepositoryService, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(pathlib.Path, "open", _raise_oserror)

    with pytest.raises(RepositoryMetadataFileSystemError):
        service.save_repository_metadata()


def test_load_repository_metadata_filesystem_error_is_metadata_scoped(
    service: RepositoryService, monkeypatch: pytest.MonkeyPatch
):
    service.save_repository_metadata()
    monkeypatch.setattr(pathlib.Path, "open", _raise_oserror)

    with pytest.raises(RepositoryMetadataFileSystemError):
        service.load_repository_metadata()


def test_add_file_missing_source_raises_resource_error(
    service: RepositoryService, tmp_path: pathlib.Path
):
    # The service performs no resource IO of its own, so this must surface as the object
    # layer's resource error rather than anything metadata scoped. A caller needs to be
    # able to tell "the content was never placed" from "the content was placed but not
    # recorded".
    with pytest.raises(RepositoryResourceFileSystemError):
        service.add_file(path=tmp_path / "does_not_exist.txt")


def test_add_directory_missing_source_raises_resource_error(
    service: RepositoryService, tmp_path: pathlib.Path
):
    with pytest.raises(RepositoryResourceFileSystemError):
        service.add_directory(path=tmp_path / "does_not_exist_dir")


# ---------------------------------------------------------------------------
# delete tolerates a resource already gone from disk
# ---------------------------------------------------------------------------


def test_delete_resource_tolerates_file_already_missing(service: RepositoryService):
    # Refusing here would leave the record permanently undeletable, since deregistration
    # never runs. The caller asked for the resource not to exist, and it does not.
    resource = service.create_file(content="x", name="x.txt")
    resource.path.unlink()

    service.delete_resource_by_resource_id(resource_id=resource.resource_id)

    with pytest.raises(ResourceNotFoundError):
        service.get_resource_by_resource_id(resource_id=resource.resource_id)


def test_delete_resource_tolerates_directory_already_missing(
    service: RepositoryService,
):
    resource = service.create_directory(name="d")
    shutil.rmtree(resource.path)

    service.delete_resource_by_resource_id(resource_id=resource.resource_id)

    with pytest.raises(ResourceNotFoundError):
        service.get_resource_by_resource_id(resource_id=resource.resource_id)
