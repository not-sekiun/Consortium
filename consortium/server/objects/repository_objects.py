import functools
import hashlib
import os
import pathlib
import shutil
import tempfile
import uuid
from collections import deque
from collections.abc import Generator
from datetime import UTC, datetime
from typing import BinaryIO, Literal, TextIO

from pydantic import JsonValue

from consortium.server.exceptions.object_exceptions.repository_object_exceptions import (
    InvalidRepositoryDirectoryArchiveFileFormatError,
    RepositoryDirectoryAlreadyExistsError,
    RepositoryDirectoryDoesNotExistError,
    RepositoryFileAlreadyExistsError,
    RepositoryFileDoesNotExistError,
    RepositoryResourceFileSystemError,
)
from consortium.server.utils import utc_now, wrap_filesystem_errors

_DEFAULT_CHUNK_SIZE = 64000  # 64 KB, mimics shutil.copyfileobj default chunk size


# The errors that mean "this resource is not on disk". Checking existence and then
# acting on the result cannot be made atomic, so a resource removed in between surfaces
# as one of these. That is the same condition the existence check itself tests for, so
# the read-only accessors below report it the way they already report a missing
# resource, as `None`, instead of raising on a race they can answer.
_RESOURCE_MISSING_ERRORS = (FileNotFoundError, NotADirectoryError)


def _filesystem_error(
    operation: str, path: pathlib.Path | str, exc: OSError
) -> RepositoryResourceFileSystemError:
    return RepositoryResourceFileSystemError(
        operation=operation,
        path=str(path),
        underlying_error=f"{type(exc).__name__}: {exc}",
    )


# Every filesystem fault touching a file or directory's own bytes is reported as
# `RepositoryResourceFileSystemError`, so the error type is bound once here rather than
# repeated at each call site. One type rather than several is deliberate: a caller cannot
# act differently on a missing path than it can on a full disk, since both mean the
# operation did not happen and the file is unchanged. The specific failure is carried in
# the error's `message` and `detail`. The default caught set (`OSError` only) is also
# deliberate: `RepositoryFile.read` can raise `UnicodeDecodeError` for a text stream the
# caller supplied, which stays unwrapped because it describes that content rather than a
# failure of the file itself.
_wrap_filesystem_errors = functools.partial(
    wrap_filesystem_errors,
    RepositoryResourceFileSystemError,
)


def _stat_or_none(path: pathlib.Path, operation: str) -> os.stat_result | None:
    # Replaces the check-then-stat pattern these accessors used to use. `stat()` is
    # itself the existence check, so this is both one syscall rather than two and free of
    # the window between them.
    try:
        return path.stat()
    except _RESOURCE_MISSING_ERRORS:
        return None
    except OSError as exc:
        raise _filesystem_error(operation=operation, path=path, exc=exc) from exc


class RepositoryFile:
    def __init__(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ):
        if isinstance(path, str):
            path = pathlib.Path(path)

        self.resource_id = uuid.uuid4()
        self.name = name if name else str(self.resource_id)
        self.description = description
        self.path = path
        self.extension = self.path.suffix  # includes the leading period
        self.datetime_created = utc_now()
        self.is_directory = False
        self.data = data if data is not None else {}

        # Must be initialized before the first compute_md5_checksum() call, or that
        # call has nothing to fall back on and crashes trying to read the cache.
        self._cached_md5_checksum = None
        # Track the tuple (size, mtime) as a fingerprint
        # to check to see if a file has been recently modified.
        self._cached_modified_fingerprint = (self.size, self.datetime_modified)
        # Store md5 checksum and only update when `force_checksum_refresh` is set or a
        # file modification is detected via the self._cached_modified_fingerprint
        self._cached_md5_checksum = None

    def __str__(self) -> str:
        return f"'{self.path}' ({self.resource_id})"

    def __repr__(self) -> str:
        return (
            f"RepositoryFile("
            f"path={self.path!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"data={self.data!r}"
            f")"
        )

    @property
    def exists_on_disk(self) -> bool:
        return self.path.exists()

    @property
    def size(self) -> int | None:
        # The size of the file is denoted as `None` rather than `0` to indicate that the
        # file is not written to disk yet.
        stat_result = _stat_or_none(self.path, operation="read the size of the file")
        return stat_result.st_size if stat_result is not None else None

    @property
    def datetime_modified(self) -> datetime | None:
        stat_result = _stat_or_none(
            self.path, operation="read the modification time of the file"
        )
        if stat_result is None:
            return None
        return datetime.fromtimestamp(stat_result.st_mtime, UTC)

    def compute_md5_checksum(self, force_checksum_refresh: bool = False) -> str | None:
        current_fingerprint = (self.size, self.datetime_modified)
        if (
            current_fingerprint == self._cached_modified_fingerprint
            and not force_checksum_refresh
        ):
            return self._cached_md5_checksum

        try:
            with self.path.open(mode="rb") as file:
                md5_hash = hashlib.md5()
                while chunk := file.read(_DEFAULT_CHUNK_SIZE):
                    md5_hash.update(chunk)
        except _RESOURCE_MISSING_ERRORS:
            # A file with no content on disk has no checksum, which is the same answer
            # this gave before the read was attempted at all.
            self._cached_md5_checksum = None
            self._cached_modified_fingerprint = current_fingerprint
            return None
        except OSError as exc:
            raise _filesystem_error(
                operation="read the file to compute its checksum",
                path=self.path,
                exc=exc,
            ) from exc

        self._cached_md5_checksum = md5_hash.hexdigest()
        self._cached_modified_fingerprint = current_fingerprint
        return self._cached_md5_checksum

    @classmethod
    def create(
        cls,
        path: pathlib.Path | str,
        content: str | bytes | TextIO | BinaryIO | None = None,
        encoding: str = "utf-8",
        exist_ok: bool = False,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ):
        if isinstance(path, str):
            path = pathlib.Path(path)

        if path.exists() and not exist_ok:
            raise RepositoryFileAlreadyExistsError(repository_file_str=str(path))

        with _wrap_filesystem_errors(operation="create the file", path=path):
            path.parent.mkdir(parents=True, exist_ok=True)

            if hasattr(content, "read"):
                first_chunk = content.read(_DEFAULT_CHUNK_SIZE)
                is_binary = isinstance(first_chunk, bytes)
                mode = "wb" if is_binary else "w"
                enc = None if is_binary else encoding
                with path.open(mode=mode, encoding=enc) as file:
                    if first_chunk:
                        file.write(first_chunk)
                    while chunk := content.read(_DEFAULT_CHUNK_SIZE):
                        file.write(chunk)
            elif isinstance(content, bytes):
                with path.open(mode="wb") as file:
                    file.write(content)
            elif isinstance(content, str):
                with path.open(mode="w", encoding=encoding) as file:
                    file.write(content)
            else:
                # content is None (or unsupported type) -> empty file, text mode
                path.touch()

        return cls(path=path, name=name, description=description, data=data)

    @classmethod
    def from_existing_path(
        cls,
        source_path: pathlib.Path | str,
        path: pathlib.Path | str,
        copy: bool = False,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ):
        # Takes a file that already exists at `source_path` and puts it at `path`, as
        # opposed to `create`, which writes new content there. As with `create`, `path` is
        # where this file comes to live: what a caller does with the resulting object is
        # its own concern and not described here. A source that is missing surfaces from
        # the move or copy itself rather than from a preceding existence check, so the
        # window between checking and acting is not left open.
        if isinstance(source_path, str):
            source_path = pathlib.Path(source_path)
        if isinstance(path, str):
            path = pathlib.Path(path)

        # The failing path is reported as the source, which is what the caller named and
        # what these operations usually fail on. When the destination is at fault instead,
        # the `OSError` carries it in its own message and reaches the caller through
        # `underlying_error`.
        with _wrap_filesystem_errors(
            operation="copy the file" if copy else "move the file",
            path=source_path,
        ):
            if copy:
                shutil.copy2(str(source_path), path)
            else:
                shutil.move(str(source_path), path)

        return cls(
            path=path,
            name=name if name else source_path.name,
            description=description,
            data=data,
        )

    def read(
        self,
        binary: bool = False,
        encoding: str = "utf-8",
        chunk_size: int | None = None,
    ) -> str | bytes | Generator[str | bytes]:
        # Checked up front so a missing file is reported when this method is called rather
        # than when a returned generator is first iterated. The opens below report the
        # same condition again for a file removed after this check: the two together mean
        # the answer is the same whether or not the read lost that race, where relying on
        # this check alone would let the raced case surface as a filesystem error.
        if not self.exists_on_disk:
            raise RepositoryFileDoesNotExistError(repository_file_str=str(self))

        mode = "rb" if binary else "r"
        encoding = None if binary else encoding

        if chunk_size is not None:
            # Rebind `chunk_size` to `size` so type checker won't complain about it
            # being nullable
            size = chunk_size

            def chunk_iterator():
                # The wrapping lives inside the generator body rather than around the
                # call that builds it, because the file is not opened until the first
                # chunk is pulled. Wrapping the enclosing method would leave the open and
                # every subsequent read unguarded.
                with _wrap_filesystem_errors(operation="read the file", path=self.path):
                    try:
                        with self.path.open(mode=mode, encoding=encoding) as file:
                            while chunk := file.read(size):
                                yield chunk
                    except _RESOURCE_MISSING_ERRORS:
                        raise RepositoryFileDoesNotExistError(
                            repository_file_str=str(self)
                        ) from None

            return chunk_iterator()
        else:
            with _wrap_filesystem_errors(operation="read the file", path=self.path):
                try:
                    with self.path.open(mode=mode, encoding=encoding) as file:
                        return file.read()
                except _RESOURCE_MISSING_ERRORS:
                    raise RepositoryFileDoesNotExistError(
                        repository_file_str=str(self)
                    ) from None

    def write(
        self,
        data: str | bytes,
        binary: bool = False,
        append: bool = False,
        encoding: str = "utf-8",
    ) -> int:
        if binary:
            mode = "ab" if append else "wb"
        else:
            mode = "a" if append else "w"
        encoding = None if isinstance(data, bytes) else encoding

        with _wrap_filesystem_errors(operation="write to the file", path=self.path):
            with self.path.open(mode=mode, encoding=encoding) as file:
                return file.write(data)

    def delete(self):
        # The missing case is reported from the unlink itself rather than from a preceding
        # existence check, so that a file removed between the two cannot surface as a
        # filesystem error. Callers key on this type to tolerate an already deleted
        # resource, and a check-then-act pair would drop them into the wrong branch
        # exactly when the resource is being removed concurrently.
        with _wrap_filesystem_errors(operation="delete the file", path=self.path):
            try:
                self.path.unlink()
            except _RESOURCE_MISSING_ERRORS:
                raise RepositoryFileDoesNotExistError(
                    repository_file_str=str(self)
                ) from None

    def to_json(
        self, include_checksum: bool = False, force_checksum_refresh: bool = False
    ) -> dict[str, JsonValue]:
        dt_modified = self.datetime_modified

        return {
            "resource_id": str(self.resource_id),
            "name": self.name,
            "description": self.description,
            "size": self.size,
            "extension": self.extension,
            "exists_on_disk": self.exists_on_disk,
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_modified": dt_modified.isoformat()
            if dt_modified is not None
            else None,
            "is_directory": self.is_directory,
            "md5_checksum": self.compute_md5_checksum(
                force_checksum_refresh=force_checksum_refresh
            )
            if include_checksum
            else None,
            "data": self.data,
        }


class RepositoryDirectory:
    def __init__(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ):
        if isinstance(path, str):
            path = pathlib.Path(path)

        self.resource_id = uuid.uuid4()
        self.name = name
        self.description = description
        self.path = path
        # Directories don't have an extension but we keep extension as `None` to be
        # symmetric with `RepositoryFile` for JSON serialization.
        self.extension = None
        self.datetime_created = utc_now()
        self.is_directory = True
        self.data = data if data is not None else {}

        # Per-file cache: relative_path: (size, mtime, md5_hex). Lets a recompute
        # skip re-reading any file whose (size, mtime) hasn't changed, instead of
        # re-hashing the whole tree's content on every single call.
        self._file_hash_cache: dict[str, tuple[int, float, str]] = {}
        self._cached_md5_checksum = None

    def __str__(self) -> str:
        if self.name is None:
            return f"'' ({self.resource_id})"
        return f"'{self.name}' ({self.resource_id})"

    def __repr__(self) -> str:
        return (
            f"RepositoryDirectory("
            f"path={self.path!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}"
            f"data={self.data!r}"
            f")"
        )

    @staticmethod
    def _hash_file_content(path: str | pathlib.Path) -> str:
        md5_hash = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(_DEFAULT_CHUNK_SIZE):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def _walk_entries(self) -> list[tuple[str, os.DirEntry | None, bool]]:
        root_path = str(self.path)
        # Normalize root path to include a separator at the end
        prefix = root_path if root_path.endswith(os.sep) else root_path + os.sep
        prefix_len = len(prefix)

        # Returns (relative_path, DirEntry, is_file) tuples, sorted by relative
        # path. Empty directories are yielded as (relative_path, None, False).
        results: list[tuple[str, os.DirEntry | None, bool]] = []
        # Manually walk directories non recursively with a stack using `os.scandir()`
        # since `pathlib.glob()` adds significant overhead creating `Path` objects
        stack = deque([root_path])
        while stack:
            current = stack.pop()
            with os.scandir(current) as iterator:
                entries = list(iterator)

            if not entries and current != root_path:
                results.append((current[prefix_len:], None, False))

            for entry in entries:
                if entry.is_dir():
                    stack.append(entry.path)
                else:
                    results.append((entry.path[prefix_len:], entry, True))

        results.sort(key=lambda item: item[0])
        return results

    @property
    def exists_on_disk(self) -> bool:
        return self.path.exists()

    @property
    def size(self) -> int | None:
        # Manually walk directories non recursively with a stack using os.scandir since
        # pathlib.glob() adds significant overhead creating `Path` objects
        total = 0
        stack = deque([str(self.path)])
        try:
            while stack:
                current = stack.pop()
                with os.scandir(current) as it:
                    for entry in it:
                        if entry.is_dir():
                            stack.append(entry.path)
                        else:
                            total += entry.stat().st_size
        except _RESOURCE_MISSING_ERRORS:
            # Either the directory itself is not on disk, or part of the tree was
            # removed while it was being walked. A total that counts only the entries
            # that happened to be visited before the removal would be a number nobody
            # can act on, so both report as `None`.
            return None
        except OSError as exc:
            raise _filesystem_error(
                operation="read the size of the directory", path=self.path, exc=exc
            ) from exc
        return total

    @property
    def datetime_modified(self) -> datetime | None:
        stat_result = _stat_or_none(
            self.path, operation="read the modification time of the directory"
        )
        if stat_result is None:
            return None
        return datetime.fromtimestamp(stat_result.st_mtime, UTC)

    def compute_md5_checksum(self, force_checksum_refresh: bool = False) -> str | None:
        overall_hash = hashlib.md5()
        seen_paths: set[str] = set()

        # Single walk: stat every entry once. Only files whose (size, mtime) have
        # actually changed since last time get their content re-read and re-hashed;
        # everything else reuses its cached per-file hash.
        try:
            walked_entries = self._walk_entries()
        except _RESOURCE_MISSING_ERRORS:
            self._file_hash_cache = {}
            self._cached_md5_checksum = None
            return None
        except OSError as exc:
            raise _filesystem_error(
                operation="walk the directory to compute its checksum",
                path=self.path,
                exc=exc,
            ) from exc

        for rel_path, entry, is_file in walked_entries:
            seen_paths.add(rel_path)

            if is_file:
                try:
                    stat_result = entry.stat()
                    size, mtime = stat_result.st_size, stat_result.st_mtime

                    cached = self._file_hash_cache.get(rel_path)
                    if (
                        not force_checksum_refresh
                        and cached is not None
                        and cached[0] == size
                        and cached[1] == mtime
                    ):
                        file_hash = cached[2]
                    else:
                        file_hash = self._hash_file_content(entry.path)
                        self._file_hash_cache[rel_path] = (size, mtime, file_hash)
                except _RESOURCE_MISSING_ERRORS:
                    # The entry was removed between the walk and being read. A checksum
                    # over a tree that is changing underneath cannot be made meaningful,
                    # so this reports the same `None` as a directory that is not there.
                    self._file_hash_cache = {}
                    self._cached_md5_checksum = None
                    return None
                except OSError as exc:
                    raise _filesystem_error(
                        operation="read a file in the directory to compute its checksum",
                        path=entry.path,
                        exc=exc,
                    ) from exc

                overall_hash.update(rel_path.encode())
                overall_hash.update(file_hash.encode())
            else:
                # Empty directories contribute their path only, no content to hash.
                overall_hash.update(rel_path.encode())

        # Drop cache entries for files that were removed or renamed since last time.
        for stale_path in set(self._file_hash_cache) - seen_paths:
            del self._file_hash_cache[stale_path]

        self._cached_md5_checksum = overall_hash.hexdigest()
        return self._cached_md5_checksum

    @classmethod
    def create(
        cls,
        path: pathlib.Path | str,
        content: bytes | BinaryIO | str | pathlib.Path | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"]
        | None = None,
        exist_ok: bool = False,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ):
        if isinstance(path, str):
            path = pathlib.Path(path)
        if isinstance(content, str):
            content = pathlib.Path(content)

        if not path.exists():
            with _wrap_filesystem_errors(operation="create the directory", path=path):
                path.mkdir()
        else:
            if not exist_ok:
                raise RepositoryDirectoryAlreadyExistsError(
                    repository_directory_str=str(path),
                )

        if isinstance(content, pathlib.Path):
            # `path` is always already created by this point (either just above via
            # mkdir(), or it pre-existed and exist_ok let us past the check) — so
            # copytree must always be told the destination exists, regardless of
            # `exist_ok`, which governs a different question (was pre-existing OK).
            with _wrap_filesystem_errors(
                operation="copy the source directory into the directory", path=path
            ):
                shutil.copytree(
                    src=content,
                    dst=path,
                    dirs_exist_ok=True,
                )
        elif hasattr(content, "read"):
            # The archive format check stays innermost so that an unreadable or
            # mismatched archive keeps reporting as an invalid archive format rather
            # than being swallowed by the surrounding filesystem error wrapping
            # (`shutil.ReadError` is itself an `OSError` subclass).
            with _wrap_filesystem_errors(
                operation="unpack the archive into the directory", path=path
            ):
                try:
                    with tempfile.TemporaryDirectory() as temp_dir_path:
                        temp_file = pathlib.Path(temp_dir_path) / "archive"
                        with temp_file.open("wb") as file:
                            while chunk := content.read(_DEFAULT_CHUNK_SIZE):
                                file.write(chunk)
                        shutil.unpack_archive(
                            filename=temp_file,
                            extract_dir=path,
                            format=archive_file_format,
                        )
                except shutil.ReadError, ValueError:
                    raise InvalidRepositoryDirectoryArchiveFileFormatError(
                        archive_file_format=archive_file_format
                    ) from None
        elif isinstance(content, bytes):
            with _wrap_filesystem_errors(
                operation="unpack the archive into the directory", path=path
            ):
                try:
                    with tempfile.TemporaryDirectory() as temp_dir_path:
                        temp_file = pathlib.Path(temp_dir_path) / "archive"
                        temp_file.write_bytes(content)
                        shutil.unpack_archive(
                            filename=temp_file,
                            extract_dir=path,
                            format=archive_file_format,
                        )
                except shutil.ReadError, ValueError:
                    raise InvalidRepositoryDirectoryArchiveFileFormatError(
                        archive_file_format=archive_file_format
                    ) from None

        return cls(path=path, name=name, description=description, data=data)

    @classmethod
    def from_existing_path(
        cls,
        source_path: pathlib.Path | str,
        path: pathlib.Path | str,
        copy: bool = False,
        name: str | None = None,
        description: str = "",
        data: dict[str, JsonValue] | None = None,
    ):
        # Takes a directory that already exists at `source_path` and puts it at `path`, as
        # opposed to `create`, which builds new content there. `copytree` is called
        # without `dirs_exist_ok` because `path` is a destination the caller has just
        # named for this directory: something already sitting there means the caller
        # picked an occupied path, which should fail rather than merge into it.
        if isinstance(source_path, str):
            source_path = pathlib.Path(source_path)
        if isinstance(path, str):
            path = pathlib.Path(path)

        # The failing path is reported as the source, which is what the caller named and
        # what these operations usually fail on. When the destination is at fault instead,
        # the `OSError` carries it in its own message and reaches the caller through
        # `underlying_error`.
        with _wrap_filesystem_errors(
            operation="copy the directory" if copy else "move the directory",
            path=source_path,
        ):
            if copy:
                shutil.copytree(str(source_path), path)
            else:
                shutil.move(str(source_path), path)

        return cls(
            path=path,
            name=name if name else source_path.name,
            description=description,
            data=data,
        )

    def delete(self) -> None:
        # Reported from the removal itself rather than from a preceding existence check,
        # for the same reason as `RepositoryFile.delete`.
        with _wrap_filesystem_errors(operation="delete the directory", path=self.path):
            try:
                shutil.rmtree(self.path)
            except _RESOURCE_MISSING_ERRORS:
                raise RepositoryDirectoryDoesNotExistError(
                    repository_directory_str=str(self),
                ) from None

    def to_json(
        self, include_checksum: bool = False, force_checksum_refresh: bool = False
    ) -> dict[str, JsonValue]:
        dt_modified = self.datetime_modified

        return {
            "resource_id": str(self.resource_id),
            "name": self.name,
            "description": self.description,
            "size": self.size,
            "extension": self.extension,
            "exists_on_disk": self.exists_on_disk,
            "md5_checksum": self.compute_md5_checksum(
                force_checksum_refresh=force_checksum_refresh
            )
            if include_checksum
            else None,
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_modified": dt_modified.isoformat()
            if dt_modified is not None
            else None,
            "is_directory": self.is_directory,
            "data": self.data,
        }
