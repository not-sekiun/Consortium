import hashlib
import pathlib
import shutil
import tempfile
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import IO, BinaryIO, Literal

from consortium.server.exceptions.framework_exceptions.repository_framework_exceptions import (
    InvalidRepositoryDirectoryArchiveFileFormatError,
    RepositoryDirectoryAlreadyExistsError,
    RepositoryDirectoryDoesNotExistError,
    RepositoryDirectoryRelativeDirectoryNotFoundError,
    RepositoryDirectoryRelativeFileAlreadyExistsError,
    RepositoryDirectoryRelativeFileNotFoundError,
    RepositoryDirectoryRelativePathIsNotAFileError,
    RepositoryDirectoryRelativePathNotFoundError,
    RepositoryFileAlreadyExistsError,
    RepositoryFileDoesNotExistError,
)


# TODO: Make async over aiofiles
class RepositoryFile:
    # TODO: Add parameter validation
    # Creating a `File` object from the constructor will simply create a new file in
    # memory but not on disk.
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
        self.datetime_updated = datetime.now()
        self.is_directory = False

    def __str__(self) -> str:
        if self.name is None:
            return f"'' ({self.resource_id})"
        return f"'{self.name}' ({self.resource_id})"

    def __repr__(self) -> str:
        return (
            f"File(path={self.path!r}, name={self.name!r}, "
            f"description={self.description!r})"
        )

    @classmethod
    def create_new_file_on_disk(
        cls,
        path: pathlib.Path | str,
        name: str | None = None,
        description: str = "",
    ) -> "RepositoryFile":
        if isinstance(path, str):
            path = pathlib.Path(path)

        file = cls(path=path, name=name, description=description)
        if not file.path.exists():
            file.create()
        return file

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
            return None
        with self.path.open(mode="rb") as file:
            md5_hash = hashlib.md5()
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                md5_hash.update(chunk)
            return md5_hash.hexdigest()

    def create(self) -> None:
        if not self.path.exists():
            self.path.touch()
        else:
            raise RepositoryFileAlreadyExistsError(repository_file_str=str(self))

    def delete(self):
        if self.path.exists():
            self.path.unlink()
        else:
            raise RepositoryFileDoesNotExistError(repository_file_str=str(self))

    def read(self, read_file_as_binary: bool = True) -> str | bytes:
        with self.open(mode="rb" if read_file_as_binary else "r") as file:
            return file.read()

    def write(self, data: str | bytes, write_file_as_binary: bool = True) -> int:
        with self.open(mode="wb" if write_file_as_binary else "w") as file:
            return file.write(data)

    def read_as_generator(
        self,
        read_file_as_binary: bool = True,
        chunk_size: int = 1024,
    ) -> Generator[str | bytes, None, None]:
        with self.open(mode="rb" if read_file_as_binary else "r") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def write_from_generator(
        self,
        data_generator: Generator[str | bytes, None, None],
        write_file_as_binary: bool = True,
    ) -> int:
        total_bytes_written = 0
        with self.open(mode="wb" if write_file_as_binary else "w") as file:
            for chunk in data_generator:
                total_bytes_written += file.write(chunk)
        return total_bytes_written

    def read_as_file_object(self, read_file_as_binary: bool = True) -> IO:
        return self.open(mode="rb" if read_file_as_binary else "r")

    def write_from_file_object(
        self,
        file_object: IO,
        write_file_as_binary: bool = True,
        chunk_size: int = 1024,
    ) -> int:
        total_bytes_written = 0
        with self.open(mode="wb" if write_file_as_binary else "w") as file:
            for chunk in iter(lambda: file_object.read(chunk_size), b""):
                total_bytes_written += file.write(chunk)
        return total_bytes_written

    def open(
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO:
        try:
            file_object = self.path.open(
                mode=mode,
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
            return file_object
        except FileNotFoundError:
            raise RepositoryFileDoesNotExistError(
                repository_file_str=str(self),
            ) from None

    def to_json(self) -> dict[str, str]:
        return {
            "resource_id": str(self.resource_id),
            "name": self.name,
            "description": self.description,
            "size": self.size,
            "exists_on_disk": self.exists_on_disk,
            "md5_checksum": self.md5_checksum,
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_updated": self.datetime_updated.isoformat(),
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
        self.datetime_updated = datetime.now()
        self.is_directory = True

    def __str__(self) -> str:
        if self.name is None:
            return f"'' ({self.resource_id})"
        return f"'{self.name}' ({self.resource_id})"

    def __repr__(self) -> str:
        return (
            f"RepositoryDirectory(path={self.path!r}, name={self.name!r}, "
            f"description={self.description!r})"
        )

    @classmethod
    def create_on_disk(
        cls,
        path: pathlib.Path | str,
        name: str | None = None,
        description="",
    ) -> "RepositoryDirectory":
        if isinstance(path, str):
            path = pathlib.Path(path)

        directory = cls(path=path, name=name, description=description)
        if not directory.path.exists():
            directory.create()
        return directory

    @classmethod
    def create_on_disk_from_archive_file_data(
        cls,
        path: pathlib.Path | str,
        archive_file_data: bytes,
        format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> "RepositoryDirectory":
        if isinstance(path, str):
            path = pathlib.Path(path)
        if format not in ("zip", "tar", "gztar", "bztar", "xztar"):
            raise InvalidRepositoryDirectoryArchiveFileFormatError

        directory = cls.create_on_disk(path=path, name=name, description=description)

        try:
            with tempfile.TemporaryDirectory() as temp_dir_path:
                temp_file = pathlib.Path(temp_dir_path) / "archive"
                temp_file.write_bytes(archive_file_data)
                shutil.unpack_archive(
                    filename=temp_file,
                    extract_dir=directory.path,
                    format=format,
                )
        except shutil.ReadError:
            raise InvalidRepositoryDirectoryArchiveFileFormatError

        return directory

    @classmethod
    def create_on_disk_from_archive_file_data_generator(
        cls,
        path: pathlib.Path | str,
        archive_file_data_generator: Generator[bytes, None, None],
        format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> "RepositoryDirectory":
        if isinstance(path, str):
            path = pathlib.Path(path)
        if format not in ("zip", "tar", "gztar", "bztar", "xztar"):
            raise InvalidRepositoryDirectoryArchiveFileFormatError

        directory = cls.create_on_disk(path=path, name=name, description=description)

        try:
            with tempfile.TemporaryDirectory() as temp_dir_path:
                temp_file = pathlib.Path(temp_dir_path) / "archive"
                with temp_file.open("wb") as file:
                    for chunk in archive_file_data_generator:
                        file.write(chunk)
                shutil.unpack_archive(
                    filename=temp_file,
                    extract_dir=directory.path,
                    format=format,
                )
        except shutil.ReadError:
            raise InvalidRepositoryDirectoryArchiveFileFormatError

        return directory

    @classmethod
    def create_on_disk_from_archive_file_data_file_object(
        cls,
        path: pathlib.Path | str,
        archive_file_data_file_object: BinaryIO,
        format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> "RepositoryDirectory":
        if isinstance(path, str):
            path = pathlib.Path(path)
        if format not in ("zip", "tar", "gztar", "bztar", "xztar"):
            raise InvalidRepositoryDirectoryArchiveFileFormatError

        directory = cls.create_on_disk(path=path, name=name, description=description)

        try:
            with tempfile.TemporaryDirectory() as temp_dir_path:
                temp_file = pathlib.Path(temp_dir_path) / "archive"
                with temp_file.open("wb") as file:
                    for chunk in iter(
                        lambda: archive_file_data_file_object.read(4096),
                        b"",
                    ):
                        file.write(chunk)
                shutil.unpack_archive(
                    filename=temp_file,
                    extract_dir=directory.path,
                    format=format,
                )
        except shutil.ReadError:
            raise InvalidRepositoryDirectoryArchiveFileFormatError

        return directory

    @property
    def exists_on_disk(self) -> bool:
        return self.path.exists()

    @property
    def size(self) -> int | None:
        if not self.exists_on_disk:
            return None
        return sum(
            file.stat().st_size for file in self.path.glob("**/*") if file.is_file()
        )

    def create(self) -> None:
        if not self.exists_on_disk:
            self.path.mkdir()
        else:
            raise RepositoryDirectoryAlreadyExistsError(
                repository_directory_str=str(self),
            )

    def delete(self, recursive: bool = False) -> None:
        if self.exists_on_disk:
            if recursive:
                shutil.rmtree(self.path)
            else:
                self.path.rmdir()
        else:
            raise RepositoryDirectoryDoesNotExistError(
                repository_directory_str=str(self),
            )

    def create_relative_file(
        self,
        relative_file_path: pathlib.Path | str,
    ) -> pathlib.Path:
        path = self.path / relative_file_path
        self._check_directory_traversal(relative_path=relative_file_path)
        if path.exists():
            raise RepositoryDirectoryRelativeFileAlreadyExistsError(
                relative_file_path=str(relative_file_path),
                repository_directory_str=str(self),
            )

        path.touch()
        return path

    def delete_relative_file(self, relative_file_path: pathlib.Path | str) -> None:
        path = self.path / relative_file_path
        self._check_directory_traversal(relative_path=relative_file_path)
        if not path.exists():
            raise RepositoryDirectoryRelativeFileNotFoundError(
                relative_file_path=str(relative_file_path),
                repository_directory_str=str(self),
            )
        if not path.is_file():
            raise RepositoryDirectoryRelativePathIsNotAFileError(
                relative_path=str(relative_file_path),
                repository_directory_str=str(self),
            )

        path.unlink()

    def read_relative_file(
        self,
        relative_file_path: pathlib.Path | str,
        read_file_as_binary: bool = True,
    ) -> str | bytes:
        with self.open_relative_file(
            relative_file_path=relative_file_path,
            mode="rb" if read_file_as_binary else "r",
        ) as file:
            return file.read()

    def write_relative_file(
        self,
        relative_file_path: pathlib.Path | str,
        data: str | bytes,
        write_file_as_binary: bool = True,
    ) -> int:
        with self.open_relative_file(
            relative_file_path=relative_file_path,
            mode="wb" if write_file_as_binary else "w",
        ) as file:
            return file.write(data)

    def read_relative_file_as_generator(
        self,
        relative_file_path: pathlib.Path | str,
        read_file_as_binary: bool = True,
        chunk_size: int = 1024,
    ) -> Generator[str | bytes, None, None]:
        with self.open_relative_file(
            relative_file_path=relative_file_path,
            mode="rb" if read_file_as_binary else "r",
        ) as file:
            while True:
                data = file.read(chunk_size)
                if data:
                    break
                yield data

    def write_relative_file_from_generator(
        self,
        data_generator: Generator[str | bytes, None, None],
        relative_file_path: pathlib.Path | str,
        write_file_as_binary: bool = True,
    ) -> None:
        with self.open_relative_file(
            relative_file_path=relative_file_path,
            mode="wb" if write_file_as_binary else "w",
        ) as file:
            for chunk in data_generator:
                file.write(chunk)

    def read_relative_file_as_file_object(
        self,
        relative_file_path: pathlib.Path | str,
        read_file_as_binary: bool = True,
    ) -> IO:
        return self.open_relative_file(
            relative_file_path=relative_file_path,
            mode="rb" if read_file_as_binary else "r",
        )

    def write_relative_file_from_file_object(
        self,
        file_object: IO,
        relative_file_path: pathlib.Path | str,
        write_file_as_binary: bool = True,
    ) -> int:
        total_bytes_written = 0
        with self.open_relative_file(
            relative_file_path=relative_file_path,
            mode="wb" if write_file_as_binary else "w",
        ) as file:
            while True:
                chunk = file_object.read(4096)
                if not chunk:
                    break
                total_bytes_written += file.write(chunk)
        return total_bytes_written

    def open_relative_file(
        self,
        relative_file_path: pathlib.Path | str,
        mode: str,
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO:
        if not self.path.exists():
            raise RepositoryDirectoryDoesNotExistError(
                repository_directory_str=str(self),
            )
        path = self.path / relative_file_path
        self._check_directory_traversal(relative_path=relative_file_path)

        try:
            return path.open(
                mode=mode,
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
        except FileNotFoundError:
            raise RepositoryDirectoryRelativeFileNotFoundError(
                relative_file_path=str(relative_file_path),
                repository_directory_str=str(self),
            )

    def create_relative_directory(
        self,
        relative_directory_path: pathlib.Path | str,
    ) -> pathlib.Path:
        path = self.path / relative_directory_path
        self._check_directory_traversal(relative_path=relative_directory_path)
        if not path.exists():
            path.mkdir()
        return path

    def delete_relative_directory(
        self,
        relative_directory_path: pathlib.Path | str,
        recursive: bool = False,
    ) -> None:
        path = self.path / relative_directory_path
        self._check_directory_traversal(relative_path=relative_directory_path)
        if not path.exists():
            raise RepositoryDirectoryRelativeDirectoryNotFoundError(
                relative_directory_path=str(relative_directory_path),
                repository_directory_str=str(self),
            )
        if not path.is_dir():
            raise RepositoryDirectoryRelativePathIsNotAFileError(
                relative_path=str(relative_directory_path),
                repository_directory_str=str(self),
            )

        if recursive:
            shutil.rmtree(path)
        else:
            path.rmdir()

    def list_relative_directory(
        self,
        relative_directory_path: pathlib.Path | str = pathlib.Path("."),
    ) -> Generator[pathlib.Path, None, None]:
        self._check_directory_traversal(relative_path=relative_directory_path)
        path = self.path / relative_directory_path
        for path_object in path.iterdir():
            yield path_object

    def walk_relative_directory(
        self,
        relative_directory_path: pathlib.Path | str = pathlib.Path("."),
    ) -> Generator[pathlib.Path, None, None]:
        path = self.path / relative_directory_path
        self._check_directory_traversal(relative_path=relative_directory_path)
        for path_object in path.glob("**/*"):
            yield path_object

    def is_relative_path_directory(self, relative_path: pathlib.Path | str):
        path = self.path / relative_path
        self._check_directory_traversal(relative_path=relative_path)
        return path.is_dir()

    def to_json(self) -> dict[str, str]:
        return {
            "resource_id": str(self.resource_id),
            "name": self.name,
            "description": self.description,
            "size": self.size,
            "exists_on_disk": self.exists_on_disk,
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_updated": self.datetime_updated.isoformat(),
            "is_directory": self.is_directory,
        }

    def _check_directory_traversal(self, relative_path: pathlib.Path) -> None:
        # Check to see if the total resolved path is still relative to the original
        # repository directory path.
        if not self.path.resolve() in (self.path / relative_path).resolve().parents:
            raise RepositoryDirectoryRelativePathNotFoundError(
                relative_path=str(relative_path),
                repository_directory_str=str(self),
            )
        if not (self.path / relative_path).exists():
            raise RepositoryDirectoryRelativePathNotFoundError(
                relative_path=str(relative_path),
                repository_directory_str=str(self),
            )
