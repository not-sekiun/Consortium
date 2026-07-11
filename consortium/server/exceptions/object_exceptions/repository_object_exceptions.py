from consortium.server.exceptions.object_exceptions.base_object_exception import (
    BaseObjectError,
)


class RepositoryObjectError(BaseObjectError):
    """Base exception for all errors that occur when operating on repository objects
    such as repository files and directories.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "REPOSITORY_OBJECT_ERROR"


class RepositoryFileError(RepositoryObjectError):
    """Base exception for all errors that occur when performing operations on a repository
    file.
    """

    code = "REPOSITORY_FILE_ERROR"


class RepositoryFileAlreadyExistsError(RepositoryFileError):
    """Raised when attempting to perform an operation on a repository file that requires
    the file to not exist but the file already exists on disk.
    """

    code = "REPOSITORY_FILE_ALREADY_EXISTS_ERROR"

    def __init__(self, repository_file_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the file {repository_file_str}. The "
            f"file already exists on the disk.",
        )


class RepositoryFileDoesNotExistError(RepositoryFileError):
    """Raised when attempting to perform an operation on a repository file that requires
    the file to exist but the file does not exist on disk.
    """

    code = "REPOSITORY_FILE_DOES_NOT_EXIST_ERROR"

    def __init__(self, repository_file_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the file {repository_file_str}. The "
            f"file does not exist on the disk.",
        )


class RepositoryDirectoryError(RepositoryObjectError):
    """Base exception for all errors that occur when performing operations on a repository
    directory.
    """

    code = "REPOSITORY_DIRECTORY_ERROR"


class RepositoryDirectoryAlreadyExistsError(RepositoryDirectoryError):
    """Raised when attempting to perform an operation on a repository directory that
    requires the directory to not exist but the directory already exists on disk.
    """

    code = "REPOSITORY_DIRECTORY_ALREADY_EXISTS_ERROR"

    def __init__(self, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"{repository_directory_str}. The directory already exists on the disk.",
        )


class RepositoryDirectoryDoesNotExistError(RepositoryDirectoryError):
    """Raised when attempting to perform an operation on a repository directory that
    requires the directory to exist but the directory does not exist on disk.
    """

    code = "REPOSITORY_DIRECTORY_DOES_NOT_EXIST_ERROR"

    def __init__(self, repository_directory_str: str) -> None:
        super().__init__(
            "Failed to perform the requested operation on the directory "
            f"{repository_directory_str}. The directory does not exist on the disk.",
        )


class RelativePathOutsideRepositoryDirectoryError(RepositoryDirectoryError):
    """Raised when a relative path provided to a repository directory operation resolves
    to a location outside of the repository directory.
    """

    code = "RELATIVE_PATH_OUTSIDE_REPOSITORY_DIRECTORY_ERROR"

    def __init__(self, relative_path: str, repository_directory_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the path '{relative_path}' "
            f"relative to the directory {repository_directory_str}. The path is outside "
            f"of the repository directory.",
        )


class RepositoryDirectoryRelativePathNotContainedError(RepositoryDirectoryError):
    """Raised when a relative path provided to a repository directory operation resolves
    to a location that is not contained within the repository directory.
    """

    code = "REPOSITORY_DIRECTORY_RELATIVE_PATH_NOT_CONTAINED_ERROR"

    def __init__(self, relative_path: str, repository_directory_str: str) -> None:
        super().__init__(
            f"Failed to perform the requested operation on the path '{relative_path}' "
            f"relative to the directory {repository_directory_str}. The path provided "
            f"when resolved is not contained within the repository directory.",
        )


class InvalidRepositoryDirectoryArchiveFileFormatError(RepositoryDirectoryError):
    """Raised when an unsupported archive file format is provided when attempting to
    create a repository directory from an archive file.
    """

    code = "INVALID_REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_ERROR"

    def __init__(self, archive_file_format: str) -> None:
        super().__init__(
            f"Failed to create a repository directory from the provided archive file. "
            f"The archive file format '{archive_file_format}' is not supported.",
        )
