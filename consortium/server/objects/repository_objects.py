import hashlib
import pathlib
import shutil
import tempfile
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import BinaryIO, Literal, TextIO

from consortium.server.exceptions.framework_exceptions.repository_framework_exceptions import (
    InvalidRepositoryDirectoryArchiveFileFormatError,
    RepositoryDirectoryAlreadyExistsError,
    RepositoryDirectoryDoesNotExistError,
    RepositoryDirectoryRelativePathNotContainedError,
    RepositoryFileAlreadyExistsError,
    RepositoryFileDoesNotExistError,
)


class RepositoryFile:
    # TODO: Add parameter validation
    def __init__(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
    ):
        if isinstance(path, str):
            path = pathlib.Path(path)

        self.resource_id = uuid.uuid4()
        self.name = name if name else str(self.resource_id)
        self.description = description
        self.path = path
        self.datetime_created = datetime.now()
        self.is_directory = False

    def __str__(self) -> str:
        return f"'{self.path}' ({self.resource_id})"

    def __repr__(self) -> str:
        return (
            f"RepositoryFile("
            f"path={self.path!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}"
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
    def md5_checksum(self) -> str | None:
        if not self.exists_on_disk:
            raise RepositoryFileDoesNotExistError(repository_file_str=str(self))
        with self.path.open(mode="rb") as file:
            md5_hash = hashlib.md5()
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                md5_hash.update(chunk)
            return md5_hash.hexdigest()

    @property
    def datetime_modified(self) -> datetime:
        if not self.exists_on_disk:
            raise RepositoryFileDoesNotExistError(repository_file_str=str(self))
        return datetime.fromtimestamp(self.path.stat().st_mtime)

    @classmethod
    def create(
        cls,
        path: pathlib.Path | str,
        content: str | bytes | TextIO | BinaryIO | None = None,
        binary: bool = False,
        encoding: str = "utf-8",
        exist_ok: bool = False,
        name: str | None = None,
        description: str = "",
    ):
        if isinstance(path, str):
            path = pathlib.Path(path)

        if not path.exists():
            path.touch()
        else:
            if not exist_ok:
                raise RepositoryFileAlreadyExistsError(
                    repository_file_str=str(path),
                )

        mode = "wb" if binary else "w"
        encoding = None if binary else encoding
        if hasattr(content, "read"):
            with path.open(mode=mode, encoding=encoding) as file:
                while chunk := content.read(4096):
                    file.write(chunk)
        elif isinstance(content, (str, bytes)):
            with path.open(mode=mode, encoding=encoding) as file:
                file.write(content)

        return cls(path=path, name=name, description=description)

    def read(
        self,
        binary: bool = False,
        encoding: str = "utf-8",
        chunk_size: int | None = None,
    ) -> str | bytes | Generator[str | bytes]:
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

    def to_json(self) -> dict[str, str]:
        return {
            "resource_id": str(self.resource_id),
            "name": self.name,
            "description": self.description,
            "size": self.size,
            "exists_on_disk": self.exists_on_disk,
            "md5_checksum": self.md5_checksum,
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_modified": self.datetime_modified.isoformat(),
            "is_directory": self.is_directory,
        }


class RepositoryDirectory:
    # TODO: Add parameter validation
    def __init__(
        self,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
    ):
        if isinstance(path, str):
            path = pathlib.Path(path)

        self.resource_id = uuid.uuid4()
        self.name = name
        self.description = description
        self.path = path
        self.datetime_created = datetime.now()
        self.is_directory = True

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
            f")"
        )

    @classmethod
    def create(
        cls,
        path: pathlib.Path | str,
        content: bytes | BinaryIO | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"]
        | None = None,
        name: str | None = None,
        description: str = "",
        exist_ok: bool = False,
    ):
        if isinstance(path, str):
            path = pathlib.Path(path)

        if not path.exists():
            path.mkdir()
        else:
            if not exist_ok:
                raise RepositoryDirectoryAlreadyExistsError(
                    repository_directory_str=str(path),
                )

        if hasattr(content, "read"):
            try:
                with tempfile.TemporaryDirectory() as temp_dir_path:
                    temp_file = pathlib.Path(temp_dir_path) / "archive"
                    with temp_file.open("wb") as file:
                        while chunk := content.read(4096):
                            file.write(chunk)
                    shutil.unpack_archive(
                        filename=temp_file,
                        extract_dir=path,
                        format=archive_file_format,
                    )
            except (shutil.ReadError, ValueError):
                raise InvalidRepositoryDirectoryArchiveFileFormatError from None
        elif isinstance(content, (str, bytes)):
            try:
                with tempfile.TemporaryDirectory() as temp_dir_path:
                    temp_file = pathlib.Path(temp_dir_path) / name
                    temp_file.write_bytes(content)
                    shutil.unpack_archive(
                        filename=temp_file,
                        extract_dir=path,
                        format=archive_file_format,
                    )
            except (shutil.ReadError, ValueError):
                raise InvalidRepositoryDirectoryArchiveFileFormatError from None

        return cls(path=path, name=name, description=description)

    @property
    def exists_on_disk(self) -> bool:
        return self.path.exists()

    @property
    def size(self) -> int | None:
        if not self.exists_on_disk:
            raise RepositoryDirectoryDoesNotExistError(
                repository_directory_str=str(self),
            )
        return sum(
            file.stat().st_size for file in self.path.glob("**/*") if file.is_file()
        )

    @property
    def datetime_modified(self) -> datetime:
        if not self.exists_on_disk:
            raise RepositoryDirectoryDoesNotExistError(
                repository_directory_str=str(self)
            )
        return datetime.fromtimestamp(self.path.stat().st_mtime)

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

        if not (self.path / relative_path).resolve().relative_to(self.path.resolve()):
            raise RepositoryDirectoryRelativePathNotContainedError(
                relative_path=str(relative_path),
                repository_directory_str=str(self),
            )

        return (self.path / relative_path).resolve()

    def to_json(self) -> dict[str, str]:
        return {
            "resource_id": str(self.resource_id),
            "name": self.name,
            "description": self.description,
            "size": self.size,
            "exists_on_disk": self.exists_on_disk,
            "md5_checksum": None,
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_modified": self.datetime_modified.isoformat(),
            "is_directory": self.is_directory,
        }
