import hashlib
import os
import pathlib
import shutil
import tempfile
import uuid
from collections import deque
from collections.abc import Generator
from datetime import datetime
from typing import BinaryIO, Literal, TextIO

from pydantic import JsonValue

from consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions import (
    InvalidRepositoryDirectoryArchiveFileFormatError,
    RepositoryDirectoryAlreadyExistsError,
    RepositoryDirectoryDoesNotExistError,
    RepositoryDirectoryRelativePathNotContainedError,
    RepositoryFileAlreadyExistsError,
    RepositoryFileDoesNotExistError,
)

_DEFAULT_CHUNK_SIZE = 64000  # 64 KB, mimics shutil.copyfileobj default chunk size


class RepositoryFile:
    # TODO: Add parameter validation
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
        self.datetime_created = datetime.now()
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
        if not self.exists_on_disk:
            return None
        return self.path.stat().st_size

    @property
    def datetime_modified(self) -> datetime | None:
        if not self.exists_on_disk:
            return None
        return datetime.fromtimestamp(self.path.stat().st_mtime)

    def compute_md5_checksum(self, force_checksum_refresh: bool = False) -> str | None:
        current_fingerprint = (self.size, self.datetime_modified)
        if (
            current_fingerprint == self._cached_modified_fingerprint
            and not force_checksum_refresh
        ):
            return self._cached_md5_checksum

        if not self.exists_on_disk:
            self._cached_md5_checksum = None
            self._cached_modified_fingerprint = current_fingerprint
            return None

        with self.path.open(mode="rb") as file:
            md5_hash = hashlib.md5()
            while chunk := file.read(_DEFAULT_CHUNK_SIZE):
                md5_hash.update(chunk)

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

    def read(
        self,
        binary: bool = False,
        encoding: str = "utf-8",
        chunk_size: int | None = None,
    ) -> str | bytes | Generator[str | bytes]:
        if not self.exists_on_disk:
            raise RepositoryFileDoesNotExistError(repository_file_str=str(self))

        mode = "rb" if binary else "r"
        encoding = None if binary else encoding

        if chunk_size is not None:

            def chunk_iterator():
                with self.path.open(mode=mode, encoding=encoding) as file:
                    while chunk := file.read(chunk_size):
                        yield chunk

            return chunk_iterator()
        else:
            with self.path.open(mode=mode, encoding=encoding) as file:
                return file.read()

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

        with self.path.open(mode=mode, encoding=encoding) as file:
            return file.write(data)

    def delete(self):
        if not self.path.exists():
            raise RepositoryFileDoesNotExistError(repository_file_str=str(self))
        self.path.unlink()

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
    # TODO: Add parameter validation
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
        self.datetime_created = datetime.now()
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
        if not self.exists_on_disk:
            return None

        # Manually walk directories non recursively with a stack using os.scandir since
        # pathlib.glob() adds significant overhead creating `Path` objects
        total = 0
        stack = deque([str(self.path)])
        while stack:
            current = stack.pop()
            with os.scandir(current) as it:
                for entry in it:
                    if entry.is_dir():
                        stack.append(entry.path)
                    else:
                        total += entry.stat().st_size
        return total

    @property
    def datetime_modified(self) -> datetime | None:
        if not self.exists_on_disk:
            return None
        return datetime.fromtimestamp(self.path.stat().st_mtime)

    def compute_md5_checksum(self, force_checksum_refresh: bool = False) -> str | None:
        if not self.exists_on_disk:
            self._file_hash_cache = {}
            self._cached_md5_checksum = None
            return None

        overall_hash = hashlib.md5()
        seen_paths: set[str] = set()

        # Single walk: stat every entry once. Only files whose (size, mtime) have
        # actually changed since last time get their content re-read and re-hashed;
        # everything else reuses its cached per-file hash.
        for rel_path, entry, is_file in self._walk_entries():
            seen_paths.add(rel_path)

            if is_file:
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
            shutil.copytree(
                src=content,
                dst=path,
                dirs_exist_ok=True,
            )
        elif hasattr(content, "read"):
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

    def delete(self) -> None:
        if not self.exists_on_disk:
            raise RepositoryDirectoryDoesNotExistError(
                repository_directory_str=str(self),
            )
        shutil.rmtree(self.path)

    def resolve_relative_path(
        self,
        relative_path: pathlib.Path | str,
    ) -> pathlib.Path:
        if isinstance(relative_path, str):
            relative_path = pathlib.Path(relative_path)

        resolved = (self.path / relative_path).resolve()
        if not resolved.is_relative_to(self.path.resolve()):
            raise RepositoryDirectoryRelativePathNotContainedError(
                relative_path=str(relative_path),
                repository_directory_str=str(self),
            ) from None

        return resolved

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
