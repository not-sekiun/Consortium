from consortium.server.exceptions.api_exceptions.http_exceptions import NotFoundError
from consortium.server.exceptions.api_exceptions.repository_api_exceptions import (
    InvalidRepositoryDirectoryArchiveFileFormatError,
    RepositoryDirectoryArchiveFileFormatNotSpecifiedError,
)


class AssetNotFoundError(NotFoundError): ...


class AssetDirectoryArchiveFileFormatNotSpecifiedError(
    RepositoryDirectoryArchiveFileFormatNotSpecifiedError,
):
    code = "ASSET_DIRECTORY_ARCHIVE_FILE_FORMAT_NOT_SPECIFIED_ERROR"

    def __init__(
        self,
    ) -> None:
        super().__init__(repository_resource_name="asset")


class InvalidAssetDirectoryArchiveFileFormatError(
    InvalidRepositoryDirectoryArchiveFileFormatError,
):
    code = "INVALID_ASSET_DIRECTORY_ARCHIVE_FILE_FORMAT_ERROR"

    def __init__(
        self,
        file_format: str,
    ) -> None:
        super().__init__(repository_resource_name="asset", file_format=file_format)
