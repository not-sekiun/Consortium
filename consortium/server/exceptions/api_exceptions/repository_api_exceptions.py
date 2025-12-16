# This module defines exceptions that are meant to be imported and subclassed by any
# other API endpoints that implement the repository API. In particular the exceptions
# defined here are used for the uploading endpoint if it is used.

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnsupportedMediaTypeError,
)


class RepositoryResourceNotFoundError(NotFoundError): ...


class RepositoryDirectoryArchiveFileFormatNotSpecifiedError(UnsupportedMediaTypeError):
    code = "REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_NOT_SPECIFIED_ERROR"

    def __init__(self) -> None:
        super().__init__(
            message=(
                "Failed to unpack uploaded repository directory archive file. The "
                "provided repository directory archive file did not have a file "
                "extension, neither was an archive file format specified. Supported "
                "archive file formats are `.zip`, `.tar`, `.tar.gz`, `.tar.xz`, and "
                "`.tar.bz2` files."
            ),
        )


class InvalidRepositoryDirectoryArchiveFileFormatError(UnsupportedMediaTypeError):
    code = "INVALID_REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_ERROR"

    def __init__(
        self,
    ) -> None:
        super().__init__(
            message=(
                "Failed to unpack uploaded repository directory archive file. The "
                "provided repository directory archive file is not valid. Check that "
                "the archive file is not corrupted or invalidly formatted."
            ),
        )


class RepositoryDirectoryFileNotArchiveFileError(UnsupportedMediaTypeError):
    code = "REPOSITORY_DIRECTORY_FILE_NOT_ARCHIVE_FILE_ERROR"

    def __init__(self, file_extension: str = "") -> None:
        if file_extension:
            super().__init__(
                message=(
                    f"Failed to unpack uploaded repository directory file. The provided "
                    f"repository directory file has the file extension "
                    f"'{file_extension}', which is not a supported archive file "
                    f"format. Supported archive file formats are `.zip`, `.tar`, "
                    f"`.tar.gz`, `.tar.xz`, and `.tar.bz2` files."
                ),
            )
        else:
            super().__init__(
                message=(
                    "Failed to unpack uploaded repository directory file. The provided "
                    "repository directory file is not a valid archive file. Supported "
                    "archive file formats are `.zip`, `.tar`, `.tar.gz`, `.tar.xz`, and "
                    "`.tar.bz2` files."
                ),
            )
