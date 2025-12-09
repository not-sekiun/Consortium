from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class RepositoryFrameworkError(BaseFrameworkException):
    code = "REPOSITORY_FRAMEWORK_ERROR"


class RepositoryFileError(RepositoryFrameworkError):
    code = "REPOSITORY_FILE_ERROR"


class RepositoryFileAlreadyExistsError(RepositoryFileError):
    code = "REPOSITORY_FILE_ALREADY_EXISTS_ERROR"

    def __init__(self, repository_file_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the file {repository_file_str}. The "
            f"file already exists on the disk.",
        )


class RepositoryFileDoesNotExistError(RepositoryFileError):
    code = "REPOSITORY_FILE_DOES_NOT_EXIST_ERROR"

    def __init__(self, repository_file_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the file {repository_file_str}. The "
            f"file does not exist on the disk.",
        )


class RepositoryDirectoryError(RepositoryFrameworkError):
    code = "REPOSITORY_DIRECTORY_ERROR"


class RepositoryDirectoryAlreadyExistsError(RepositoryDirectoryError):
    code = "REPOSITORY_DIRECTORY_ALREADY_EXISTS_ERROR"

    def __init__(self, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"{repository_directory_str}. The directory already exists on the disk.",
        )


class RepositoryDirectoryDoesNotExistError(RepositoryDirectoryError):
    code = "REPOSITORY_DIRECTORY_DOES_NOT_EXIST_ERROR"

    def __init__(self, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"{repository_directory_str}. The directory does not exist on the disk.",
        )


class RepositoryDirectoryRelativePathNotFoundError(RepositoryDirectoryError):
    code = "REPOSITORY_DIRECTORY_RELATIVE_PATH_NOT_FOUND_ERROR"

    def __init__(self, relative_path: str, repository_directory_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the path '{relative_path}' "
            f"relative to the directory {repository_directory_str}. The path does "
            f"not exist on the disk.",
        )


class RepositoryDirectoryRelativeFileAlreadyExistsError(RepositoryDirectoryError):
    code = "REPOSITORY_DIRECTORY_RELATIVE_FILE_ALREADY_EXISTS_ERROR"

    def __init__(self, relative_file_path: str, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the file "
            f"'{relative_file_path}' relative to the directory "
            f"{repository_directory_str}. The file already exists on the disk.",
        )


class RepositoryDirectoryRelativeFileNotFoundError(RepositoryDirectoryError):
    code = "REPOSITORY_DIRECTORY_RELATIVE_FILE_NOT_FOUND_ERROR"

    def __init__(self, relative_file_path: str, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the file "
            f"'{relative_file_path}' relative to the directory "
            f"{repository_directory_str}. The file does not exist on the disk.",
        )


class RepositoryDirectoryRelativePathIsNotAFileError(RepositoryDirectoryError):
    code = "REPOSITORY_DIRECTORY_RELATIVE_PATH_IS_NOT_A_FILE_ERROR"

    def __init__(self, relative_path: str, repository_directory_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the path '{relative_path}' "
            f"relative to the directory {repository_directory_str}. The path is not a "
            "file.",
        )


class RepositoryDirectoryRelativeDirectoryNotFoundError(RepositoryDirectoryError):
    code = "REPOSITORY_DIRECTORY_RELATIVE_DIRECTORY_NOT_FOUND_ERROR"

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
    code = "INVALID_REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_ERROR"

    def __init__(self) -> None:
        super().__init__(
            "Failed to create the directory. The format of the provided archive file "
            "data is invalid. Only 'zip', 'tar', 'gztar', 'xztar', and 'bztar' archive "
            "file formats are supported.",
        )
