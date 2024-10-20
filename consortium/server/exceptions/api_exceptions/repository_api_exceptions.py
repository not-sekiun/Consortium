# This module defines exceptions that are meant to be imported and subclassed by any
# other API endpoints that implement the repository API. In particular the exceptions
# defined here are used for the uploading endpoint if it is used.

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    UnsupportedMediaTypeError,
)


class RepositoryDirectoryArchiveFileFormatNotSpecifiedError(UnsupportedMediaTypeError):
    code = "REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_NOT_SPECIFIED_ERROR"

    def __init__(self, repository_resource_name: str = "repository") -> None:
        super().__init__(
            message=(
                f"Failed to unpack uploaded {repository_resource_name} directory archive "
                f"file. The provided {repository_resource_name} directory archive file "
                "did not have a file extension, neither was an archive file format "
                "specified. Supported archive file formats are zip, tar, tar.gz, "
                "tar.xz, and tar.bz2 files."
            ),
        )


class InvalidRepositoryDirectoryArchiveFileFormatError(UnsupportedMediaTypeError):
    code = "INVALID_REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_ERROR"

    def __init__(
        self,
        file_format: str,
        repository_resource_name: str = "repository",
    ) -> None:
        super().__init__(
            message=(
                f"Failed to unpack uploaded {repository_resource_name} directory archive "
                f"file. The provided {repository_resource_name} directory archive file "
                f"format '{file_format}' is not supported. Supported archive file "
                f"formats are .zip, .tar, .tar.gz, .tar.xz, and .tar.bz2 files."
            ),
        )
