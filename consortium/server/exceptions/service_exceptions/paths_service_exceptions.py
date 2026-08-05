"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`PathsServiceError`][consortium.server.exceptions.service_exceptions.paths_service_exceptions.PathsServiceError]
        - [`ConsortiumUserAccountsFileSystemError`][consortium.server.exceptions.service_exceptions.paths_service_exceptions.ConsortiumUserAccountsFileSystemError]
        - [`ConsortiumRolePermissionsFileSystemError`][consortium.server.exceptions.service_exceptions.paths_service_exceptions.ConsortiumRolePermissionsFileSystemError]
        - [`ConsortiumReleaseFileSystemError`][consortium.server.exceptions.service_exceptions.paths_service_exceptions.ConsortiumReleaseFileSystemError]
        - [`ConsortiumDirectoryFileSystemError`][consortium.server.exceptions.service_exceptions.paths_service_exceptions.ConsortiumDirectoryFileSystemError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class PathsServiceError(BaseServiceError):
    """Base exception for all errors that occur within the paths service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "PATHS_SERVICE_ERROR"


class ConsortiumUserAccountsFileSystemError(PathsServiceError):
    """Raised when the paths service cannot confirm the user accounts file is present
    on disk as a preflight check at server startup.

    This is distinct from
    [`UserAccountsFileSystemError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileSystemError],
    which the user accounts service raises when it later reads or writes the file. This
    error is raised earlier, during the paths service's own startup preflight, before
    the user accounts service ever touches the file.
    """

    code = "CONSORTIUM_USER_ACCOUNTS_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=(
                f"Failed to {operation} at the path '{path}'. {underlying_error} If "
                f"the file is missing, create it before starting the server. If a "
                f"directory exists at this path instead of a file, delete or move it "
                f"and put the file there instead, then restart the server."
            ),
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class ConsortiumRolePermissionsFileSystemError(PathsServiceError):
    """Raised when the paths service cannot confirm the role permissions file is
    present on disk as a preflight check at server startup.

    This is distinct from
    [`RolePermissionsFileSystemError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFileSystemError],
    which the authorization service raises when it later reads or writes the file. This
    error is raised earlier, during the paths service's own startup preflight, before
    the authorization service ever touches the file.
    """

    code = "CONSORTIUM_ROLE_PERMISSIONS_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=(
                f"Failed to {operation} at the path '{path}'. {underlying_error} If "
                f"the file is missing, create it before starting the server. If a "
                f"directory exists at this path instead of a file, delete or move it "
                f"and put the file there instead, then restart the server."
            ),
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class ConsortiumReleaseFileSystemError(PathsServiceError):
    """Raised when the paths service cannot confirm the release JSON file is present
    on disk as a preflight check at server startup.

    This is distinct from
    [`ReleaseFileSystemError`][consortium.server.exceptions.service_exceptions.release_service_exceptions.ReleaseFileSystemError],
    which the release service raises when it later reads the file. This error is raised
    earlier, during the paths service's own startup preflight, before the release
    service ever touches the file.
    """

    code = "CONSORTIUM_RELEASE_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=(
                f"Failed to {operation} at the path '{path}'. {underlying_error} If "
                f"the file is missing, create it before starting the server. If a "
                f"directory exists at this path instead of a file, delete or move it "
                f"and put the file there instead, then restart the server."
            ),
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class ConsortiumDirectoryFileSystemError(PathsServiceError):
    """Raised when the paths service cannot confirm or create one of the directories
    it expects to exist, as a preflight check at server startup."""

    code = "CONSORTIUM_DIRECTORY_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=(
                f"Failed to {operation} at the path '{path}'. {underlying_error} "
                f"Ensure a directory can exist at this path: delete or move any file "
                f"occupying it, replacing it with the corresponding directory, and "
                f"confirm the server process has permission to create directories "
                f"there, then restart the server."
            ),
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )
