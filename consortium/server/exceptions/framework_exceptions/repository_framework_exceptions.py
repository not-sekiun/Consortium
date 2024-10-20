from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class RepositoryFrameworkError(BaseFrameworkException):
    pass


class RepositoryFileError(RepositoryFrameworkError):
    pass


class RepositoryFileAlreadyExistsError(RepositoryFileError):
    def __init__(self, repository_file_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the file {repository_file_str}. The "
            f"file already exists on the disk.",
        )


class RepositoryFileDoesNotExistError(RepositoryFileError):
    def __init__(self, repository_file_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the file {repository_file_str}. The "
            f"file does not exist on the disk.",
        )


class RepositoryDirectoryError(RepositoryFrameworkError):
    pass


class RepositoryDirectoryAlreadyExistsError(RepositoryDirectoryError):
    def __init__(self, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"{repository_directory_str}. The directory already exists on the disk.",
        )


class RepositoryDirectoryDoesNotExistError(RepositoryDirectoryError):
    def __init__(self, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"{repository_directory_str}. The directory does not exist on the disk.",
        )


class RepositoryDirectoryRelativePathNotFoundError(RepositoryDirectoryError):
    def __init__(self, relative_path: str, repository_directory_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the path '{relative_path}' "
            f"relative to the directory {repository_directory_str}. The path does "
            f"not exist on the disk.",
        )


class RepositoryDirectoryRelativeFileAlreadyExistsError(RepositoryDirectoryError):
    def __init__(self, relative_file_path: str, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the file "
            f"'{relative_file_path}' relative to the directory "
            f"{repository_directory_str}. The file already exists on the disk.",
        )


class RepositoryDirectoryRelativeFileNotFoundError(RepositoryDirectoryError):
    def __init__(self, relative_file_path: str, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the file "
            f"'{relative_file_path}' relative to the directory "
            f"{repository_directory_str}. The file does not exist on the disk.",
        )


class RepositoryDirectoryRelativePathIsNotAFileError(RepositoryDirectoryError):
    def __init__(self, relative_path: str, repository_directory_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the path '{relative_path}' "
            f"relative to the directory {repository_directory_str}. The path is not a "
            "file.",
        )


class RepositoryDirectoryRelativeDirectoryNotFoundError(RepositoryDirectoryError):
    def __init__(
        self,
        relative_directory_path: str,
        repository_directory_str: str,
    ) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"'{relative_directory_path}' relative to the directory "
            f"{repository_directory_str}. The directory does not exist on the disk.",
        )


class InvalidRepositoryDirectoryArchiveFileFormatError(RepositoryDirectoryError):
    def __init__(self) -> None:
        super().__init__(
            "Failed to create the directory. The format of the provided archive file "
            "data is invalid. Only 'zip', 'tar', 'gztar', 'xztar', and 'bztar' archive "
            "file formats are supported.",
        )
