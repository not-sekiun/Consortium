# This module defines exceptions that are meant to be imported and subclassed by any
# other API endpoints that implement the repository API. In particular the exceptions
# defined here are used for the uploading endpoint if it is used.

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    InternalServerError,
    NotFoundError,
    UnsupportedMediaTypeError,
)


class RepositoryResourceNotFoundError(NotFoundError): ...


class UnsyncedRepositoryResourceError(InternalServerError):
    """Raised when a resource's content is requested but the file or directory it is
    recorded against no longer exists in the repository directory.

    This is a server side fault rather than a client one, so it is a 500. The resource is
    known to the repository, is listed by its collection endpoint and serves its metadata
    normally, and the server simply cannot produce content it advertises. Nothing about
    the request is wrong and no change to it would succeed.

    It is deliberately neither a 404, which is already used on these endpoints for a
    resource ID the repository does not know and would make the two indistinguishable,
    nor a 410, which asserts a permanence the server has no way to determine: the content
    may yet be restored from a backup or a remounted volume.

    Note that a resource in this state can still be deleted. Deletion tolerates missing
    content because the caller's intent is already satisfied, whereas a read cannot be
    satisfied at all.
    """

    code = "UNSYNCED_REPOSITORY_RESOURCE_ERROR"

    def __init__(self, resource_id: str = "<resource_id>") -> None:
        super().__init__(
            message=(
                "Failed to read the content of the repository resource with the "
                f"resource ID '{resource_id}'. The resource is recorded in the "
                "repository metadata but its content no longer exists in the repository "
                "directory, which has been modified outside of the server."
            ),
            detail={"resource_id": resource_id},
        )


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
