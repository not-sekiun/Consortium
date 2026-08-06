import pathlib

import pytest

from consortium.server.exceptions.object_exceptions.repository_object_exceptions import (
    RepositoryDirectoryDoesNotExistError,
    RepositoryFileDoesNotExistError,
    RepositoryResourceFileSystemError,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)


@pytest.fixture
def source_file(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "source.txt"
    path.write_text("content", encoding="utf-8")
    return path


@pytest.fixture
def source_directory(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "source_dir"
    path.mkdir()
    (path / "inner.txt").write_text("inner", encoding="utf-8")
    return path


@pytest.fixture
def destination(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "destination"
    path.mkdir()
    return path


# ---------------------------------------------------------------------------
# RepositoryFile.from_existing_path
# ---------------------------------------------------------------------------


def test_file_from_existing_path_moves_by_default(
    source_file: pathlib.Path, destination: pathlib.Path
):
    target = destination / "moved.txt"

    repository_file = RepositoryFile.from_existing_path(
        source_path=source_file, path=target
    )

    assert repository_file.path == target
    assert target.read_text(encoding="utf-8") == "content"
    assert not source_file.exists()


def test_file_from_existing_path_copy_leaves_source(
    source_file: pathlib.Path, destination: pathlib.Path
):
    target = destination / "copied.txt"

    RepositoryFile.from_existing_path(source_path=source_file, path=target, copy=True)

    assert target.read_text(encoding="utf-8") == "content"
    assert source_file.exists()


def test_file_from_existing_path_defaults_name_to_source_name(
    source_file: pathlib.Path, destination: pathlib.Path
):
    repository_file = RepositoryFile.from_existing_path(
        source_path=source_file, path=destination / "renamed.txt"
    )

    assert repository_file.name == "source.txt"


def test_file_from_existing_path_accepts_string_paths(
    source_file: pathlib.Path, destination: pathlib.Path
):
    target = destination / "moved.txt"

    repository_file = RepositoryFile.from_existing_path(
        source_path=str(source_file), path=str(target)
    )

    assert repository_file.path == target


def test_file_from_existing_path_missing_source_raises(
    tmp_path: pathlib.Path, destination: pathlib.Path
):
    with pytest.raises(RepositoryResourceFileSystemError):
        RepositoryFile.from_existing_path(
            source_path=tmp_path / "absent.txt", path=destination / "moved.txt"
        )


def test_file_from_existing_path_error_message_omits_repository_vocabulary(
    tmp_path: pathlib.Path, destination: pathlib.Path
):
    # A `RepositoryFile` only tracks a file: it has no idea whether a repository is what
    # the caller is putting it into, so the failure must not claim otherwise.
    with pytest.raises(RepositoryResourceFileSystemError) as exc_info:
        RepositoryFile.from_existing_path(
            source_path=tmp_path / "absent.txt", path=destination / "moved.txt"
        )

    assert "repository" not in exc_info.value.detail["operation"]


# ---------------------------------------------------------------------------
# RepositoryDirectory.from_existing_path
# ---------------------------------------------------------------------------


def test_directory_from_existing_path_moves_by_default(
    source_directory: pathlib.Path, destination: pathlib.Path
):
    target = destination / "moved_dir"

    repository_directory = RepositoryDirectory.from_existing_path(
        source_path=source_directory, path=target
    )

    assert repository_directory.path == target
    assert (target / "inner.txt").read_text(encoding="utf-8") == "inner"
    assert not source_directory.exists()


def test_directory_from_existing_path_copy_leaves_source(
    source_directory: pathlib.Path, destination: pathlib.Path
):
    target = destination / "copied_dir"

    RepositoryDirectory.from_existing_path(
        source_path=source_directory, path=target, copy=True
    )

    assert (target / "inner.txt").read_text(encoding="utf-8") == "inner"
    assert source_directory.exists()


def test_directory_from_existing_path_defaults_name_to_source_name(
    source_directory: pathlib.Path, destination: pathlib.Path
):
    repository_directory = RepositoryDirectory.from_existing_path(
        source_path=source_directory, path=destination / "renamed_dir"
    )

    assert repository_directory.name == "source_dir"


def test_directory_from_existing_path_missing_source_raises(
    tmp_path: pathlib.Path, destination: pathlib.Path
):
    with pytest.raises(RepositoryResourceFileSystemError):
        RepositoryDirectory.from_existing_path(
            source_path=tmp_path / "absent_dir", path=destination / "moved_dir"
        )


# ---------------------------------------------------------------------------
# a resource missing from disk is reported as missing, not as a filesystem fault
# ---------------------------------------------------------------------------


def test_file_delete_missing_raises_does_not_exist(tmp_path: pathlib.Path):
    repository_file = RepositoryFile(path=tmp_path / "absent.txt")

    with pytest.raises(RepositoryFileDoesNotExistError):
        repository_file.delete()


def test_directory_delete_missing_raises_does_not_exist(tmp_path: pathlib.Path):
    repository_directory = RepositoryDirectory(path=tmp_path / "absent_dir")

    with pytest.raises(RepositoryDirectoryDoesNotExistError):
        repository_directory.delete()


def test_file_read_missing_raises_does_not_exist(tmp_path: pathlib.Path):
    repository_file = RepositoryFile(path=tmp_path / "absent.txt")

    with pytest.raises(RepositoryFileDoesNotExistError):
        repository_file.read()


def test_file_delete_reports_real_filesystem_faults_as_such(tmp_path: pathlib.Path):
    # The catch that converts a missing resource must stay narrow: a fault that is not
    # "it is not there" has to keep reporting as a filesystem error, or callers keyed on
    # the missing case would silently swallow genuine failures. Unlinking a directory is
    # a fault of that kind on every platform.
    repository_file = RepositoryFile(path=tmp_path)

    with pytest.raises(RepositoryResourceFileSystemError):
        repository_file.delete()


# ---------------------------------------------------------------------------
# losing the check-then-act race still reports the resource as missing
# ---------------------------------------------------------------------------


def test_file_read_reports_missing_when_removed_after_the_existence_check(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    # Simulates the file being deleted between `read`'s existence check and its open.
    # Before the operation reported this condition itself, the raced case surfaced as a
    # filesystem error while the ordinary case raised the missing type, so the answer
    # depended on timing.
    repository_file = RepositoryFile(path=tmp_path / "absent.txt")
    monkeypatch.setattr(
        RepositoryFile, "exists_on_disk", property(lambda self: True), raising=False
    )

    with pytest.raises(RepositoryFileDoesNotExistError):
        repository_file.read()


def test_chunked_file_read_reports_missing_when_removed_after_the_existence_check(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    # The chunked path opens the file lazily on first iteration, so it races over a
    # wider window than the eager one and must reach the same answer.
    repository_file = RepositoryFile(path=tmp_path / "absent.txt")
    monkeypatch.setattr(
        RepositoryFile, "exists_on_disk", property(lambda self: True), raising=False
    )

    with pytest.raises(RepositoryFileDoesNotExistError):
        list(repository_file.read(chunk_size=8))


# ---------------------------------------------------------------------------
# RepositoryFile.create / RepositoryDirectory.create content typing
# ---------------------------------------------------------------------------


def test_file_create_with_no_content_makes_an_empty_file(tmp_path: pathlib.Path):
    repository_file = RepositoryFile.create(path=tmp_path / "empty.txt")

    assert repository_file.path.is_file()
    assert repository_file.path.read_text(encoding="utf-8") == ""


def test_file_create_rejects_unsupported_content(tmp_path: pathlib.Path):
    # Anything that is neither a string, bytes nor a readable file object used to fall
    # through to `touch()`, so the caller got an empty file and no indication that the
    # content had been dropped. A generator is the case that motivated this: it reads
    # as a plausible way to supply content and writes nothing at all.
    def _chunks():
        yield "written"

    with pytest.raises(TypeError):
        RepositoryFile.create(path=tmp_path / "generator.txt", content=_chunks())

    with pytest.raises(TypeError):
        RepositoryFile.create(path=tmp_path / "integer.txt", content=1)


def test_file_create_leaves_nothing_behind_when_content_is_rejected(
    tmp_path: pathlib.Path,
):
    # The type is checked before the parent directories are made, so a rejected call
    # does not leave a half-created tree.
    path = tmp_path / "nested" / "generator.txt"

    with pytest.raises(TypeError):
        RepositoryFile.create(path=path, content=(chunk for chunk in ("a", "b")))

    assert not path.exists()
    assert not path.parent.exists()


def test_directory_create_with_no_content_makes_an_empty_directory(
    tmp_path: pathlib.Path,
):
    repository_directory = RepositoryDirectory.create(path=tmp_path / "empty_dir")

    assert repository_directory.path.is_dir()
    assert list(repository_directory.path.iterdir()) == []


def test_directory_create_rejects_unsupported_content(tmp_path: pathlib.Path):
    # The directory path had no fallback branch at all, so unsupported content was
    # silently ignored and left an empty directory behind.
    def _chunks():
        yield b"archive"

    with pytest.raises(TypeError):
        RepositoryDirectory.create(path=tmp_path / "generator_dir", content=_chunks())


def test_directory_create_leaves_nothing_behind_when_content_is_rejected(
    tmp_path: pathlib.Path,
):
    path = tmp_path / "generator_dir"

    with pytest.raises(TypeError):
        RepositoryDirectory.create(path=path, content=(chunk for chunk in (b"a", b"b")))

    assert not path.exists()


# ---------------------------------------------------------------------------
# a resource's name is held verbatim and is independent of its path
# ---------------------------------------------------------------------------


def test_file_name_is_held_verbatim_including_its_extension(tmp_path: pathlib.Path):
    # The name is the name the resource is served and downloaded under, so nothing is
    # stripped from it, and the path it happens to be stored at does not shape it.
    repository_file = RepositoryFile(path=tmp_path / "abcd-1234", name="report.tar.gz")

    assert repository_file.name == "report.tar.gz"


def test_file_name_falls_back_to_the_resource_id(tmp_path: pathlib.Path):
    repository_file = RepositoryFile(path=tmp_path / "abcd-1234")

    assert repository_file.name == str(repository_file.resource_id)


def test_directory_name_is_held_verbatim(tmp_path: pathlib.Path):
    repository_directory = RepositoryDirectory(
        path=tmp_path / "abcd-1234", name="collection.v2"
    )

    assert repository_directory.name == "collection.v2"


def test_directory_name_falls_back_to_the_resource_id(tmp_path: pathlib.Path):
    repository_directory = RepositoryDirectory(path=tmp_path / "abcd-1234")

    assert repository_directory.name == str(repository_directory.resource_id)


def test_file_to_json_carries_the_whole_name_and_no_extension(tmp_path: pathlib.Path):
    path = tmp_path / "abcd-1234"
    path.write_text("content", encoding="utf-8")
    repository_file = RepositoryFile(path=path, name="report.tar.gz")

    resource_json = repository_file.to_json()

    assert resource_json["name"] == "report.tar.gz"
    assert "extension" not in resource_json


def test_directory_to_json_carries_no_extension(tmp_path: pathlib.Path):
    path = tmp_path / "abcd-1234"
    path.mkdir()
    repository_directory = RepositoryDirectory(path=path, name="collection.v2")

    resource_json = repository_directory.to_json()

    assert resource_json["name"] == "collection.v2"
    assert "extension" not in resource_json
