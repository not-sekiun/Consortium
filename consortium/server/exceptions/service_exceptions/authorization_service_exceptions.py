"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`AuthorizationServiceError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.AuthorizationServiceError]
        - [`RolePermissionsFileError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFileError]
            - [`RolePermissionsFileSystemError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFileSystemError]
            - [`RolePermissionsFileContentError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFileContentError]
                - [`RolePermissionsFileEncodingError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFileEncodingError]
                - [`RolePermissionsFileJSONError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFileJSONError]
                - [`RolePermissionsFileSchemaError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFileSchemaError]
                - [`RolePermissionsFilePermissionValueError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFilePermissionValueError]
        - [`RoleNotFoundError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RoleNotFoundError]
        - [`RoleAlreadyExistsError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RoleAlreadyExistsError]
        - [`PermissionNotInRoleError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.PermissionNotInRoleError]
        - [`PermissionAlreadyInRoleError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.PermissionAlreadyInRoleError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class AuthorizationServiceError(BaseServiceError):
    """Base exception for all errors that occur within the authorization service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "AUTHORIZATION_SERVICE_ERROR"


class RolePermissionsFileError(AuthorizationServiceError):
    """Base exception for every failure to get the role permissions file's data on or
    off disk.

    Catch this to handle "the role permissions did not make it in or out" without caring
    why. To distinguish a filesystem fault from a bad file, catch
    `RolePermissionsFileSystemError` or `RolePermissionsFileContentError` instead.
    """

    code = "ROLE_PERMISSIONS_FILE_ERROR"


class RolePermissionsFileSystemError(RolePermissionsFileError):
    """Raised when the role permissions file cannot be read from or written to disk.

    This covers every way the filesystem can refuse the operation: the file does not
    exist, the process lacks the required permissions, the configured path points at a
    directory, the disk is full. They share one type because no caller can act differently
    on any of them. All of them mean the operation did not happen, and the specific cause
    is carried in `message` and `detail` for whoever has to fix it.

    Collapsing every filesystem fault into one type matters more here than elsewhere in
    the framework. `PermissionError` is a builtin `OSError` subclass, and this service's
    entire domain is authorization permissions, so a raw, unwrapped `PermissionError`
    reads to a caller as an authorization decision (a role lacking a permission) rather
    than what it actually is (the OS denying access to the file on disk). Routing every
    filesystem failure, including `PermissionError`, through this single named type
    removes that ambiguity: a caller that sees `RolePermissionsFileSystemError` knows
    immediately the failure is about the file, not about a role's permissions.

    A file the filesystem hands over successfully but whose contents are wrong is reported
    separately, through `RolePermissionsFileContentError`.
    """

    code = "ROLE_PERMISSIONS_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=f"Failed to {operation} at the path '{path}'. {underlying_error}",
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class RolePermissionsFileContentError(RolePermissionsFileError):
    """Base exception for all errors that occur when a role permissions file's contents
    are wrong.

    The filesystem handed the file's bytes over successfully, so this is fixed by
    correcting the file rather than by changing the state of the machine or the
    configured path.
    """

    code = "ROLE_PERMISSIONS_FILE_CONTENT_ERROR"


class RolePermissionsFileEncodingError(RolePermissionsFileContentError):
    """Raised when a role permissions file's bytes cannot be decoded as UTF-8."""

    code = "ROLE_PERMISSIONS_FILE_ENCODING_ERROR"

    def __init__(self, path: str, underlying_error: str):
        super().__init__(
            message=(
                f"Failed to load the role permissions file '{path}'. "
                f"The file's contents are not valid UTF-8 text. {underlying_error}"
            ),
            detail={
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class RolePermissionsFileJSONError(RolePermissionsFileContentError):
    """Raised when a role permissions file cannot be parsed as valid JSON."""

    code = "ROLE_PERMISSIONS_FILE_JSON_ERROR"

    def __init__(self, path: str):
        super().__init__(
            message=(
                f"Failed to load the role permissions file '{path}'. "
                f"The file is not valid JSON."
            ),
            detail={"path": path},
        )


class RolePermissionsFileSchemaError(RolePermissionsFileContentError):
    """Raised when a role permissions file does not conform to the expected JSON schema."""

    code = "ROLE_PERMISSIONS_FILE_SCHEMA_ERROR"

    def __init__(self, path: str, json_schema_error_message: str):
        super().__init__(
            message=(
                f"Failed to load the role permissions file '{path}'. "
                f"The file does not conform to the expected JSON schema. "
                f"{json_schema_error_message}"
            ),
            detail={
                "path": path,
                "json_schema_error_message": json_schema_error_message,
            },
        )


class RolePermissionsFilePermissionValueError(RolePermissionsFileContentError):
    """Raised when a role permissions file contains an unrecognised permission value."""

    code = "ROLE_PERMISSIONS_FILE_PERMISSION_VALUE_ERROR"

    def __init__(self, path: str, role: str, permission: str):
        super().__init__(
            message=(
                f"Failed to load the role permissions file '{path}'. "
                f"The permission '{permission}' assigned to role '{role}' is not a "
                f"recognised UserPermissions value."
            ),
            detail={"path": path, "role": role, "permission": permission},
        )


class RoleNotFoundError(AuthorizationServiceError):
    """Raised when the requested role does not exist in the authorization service."""

    code = "ROLE_NOT_FOUND_ERROR"

    def __init__(self, role: str):
        super().__init__(
            message=(
                f"Failed to find the requested role. No role named '{role}' exists in "
                f"the authorization service."
            ),
            detail={"role": role},
        )


class RoleAlreadyExistsError(AuthorizationServiceError):
    """Raised when attempting to create a role that already exists."""

    code = "ROLE_ALREADY_EXISTS_ERROR"

    def __init__(self, role: str):
        super().__init__(
            message=(
                f"Failed to create role '{role}'. A role with that name already exists "
                f"in the authorization service."
            ),
            detail={"role": role},
        )


class PermissionNotInRoleError(AuthorizationServiceError):
    """Raised when the requested permission is not assigned to the specified role."""

    code = "PERMISSION_NOT_IN_ROLE_ERROR"

    def __init__(self, role: str, permission: str):
        super().__init__(
            message=(
                f"Failed to find the requested permission. The permission '{permission}' "
                f"is not assigned to role '{role}'."
            ),
            detail={"role": role, "permission": permission},
        )


class PermissionAlreadyInRoleError(AuthorizationServiceError):
    """Raised when attempting to add a permission that is already assigned to the role."""

    code = "PERMISSION_ALREADY_IN_ROLE_ERROR"

    def __init__(self, role: str, permission: str):
        super().__init__(
            message=(
                f"Failed to add permission '{permission}' to role '{role}'. That "
                f"permission is already assigned to that role."
            ),
            detail={"role": role, "permission": permission},
        )
