"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`AuthorizationServiceError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.AuthorizationServiceError]
        - [`RolePermissionsFileSystemError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.RolePermissionsFileSystemError]
        - [`InvalidRolePermissionsFileError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.InvalidRolePermissionsFileError]
            - [`InvalidRolePermissionsFileEncodingError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.InvalidRolePermissionsFileEncodingError]
            - [`InvalidRolePermissionsFileJSONError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.InvalidRolePermissionsFileJSONError]
            - [`InvalidRolePermissionsFileSchemaError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.InvalidRolePermissionsFileSchemaError]
            - [`InvalidRolePermissionsFilePermissionValueError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.InvalidRolePermissionsFilePermissionValueError]
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


class RolePermissionsFileSystemError(AuthorizationServiceError):
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
    separately, through `InvalidRolePermissionsFileEncodingError`,
    `InvalidRolePermissionsFileJSONError`, `InvalidRolePermissionsFileSchemaError` or
    `InvalidRolePermissionsFilePermissionValueError`.
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


class InvalidRolePermissionsFileError(AuthorizationServiceError):
    """Base exception for errors when reading or writing a role permissions file."""

    code = "INVALID_ROLE_PERMISSIONS_FILE_ERROR"


class InvalidRolePermissionsFileEncodingError(InvalidRolePermissionsFileError):
    """Raised when a role permissions file's bytes cannot be decoded as UTF-8."""

    code = "INVALID_ROLE_PERMISSIONS_FILE_ENCODING_ERROR"

    def __init__(self, file_path: str, underlying_error: str):
        super().__init__(
            message=(
                f"Failed to load the role permissions file '{file_path}'. "
                f"The file's contents are not valid UTF-8 text. {underlying_error}"
            ),
            detail={
                "file_path": file_path,
                "underlying_error": underlying_error,
            },
        )


class InvalidRolePermissionsFileJSONError(InvalidRolePermissionsFileError):
    """Raised when a role permissions file cannot be parsed as valid JSON."""

    code = "INVALID_ROLE_PERMISSIONS_FILE_JSON_ERROR"

    def __init__(self, file_path: str):
        super().__init__(
            message=(
                f"Failed to load the role permissions file '{file_path}'. "
                f"The file is not valid JSON."
            ),
            detail={"file_path": file_path},
        )


class InvalidRolePermissionsFileSchemaError(InvalidRolePermissionsFileError):
    """Raised when a role permissions file does not conform to the expected JSON schema."""

    code = "INVALID_ROLE_PERMISSIONS_FILE_SCHEMA_ERROR"

    def __init__(self, file_path: str, json_schema_error_message: str):
        super().__init__(
            message=(
                f"Failed to load the role permissions file '{file_path}'. "
                f"The file does not conform to the expected JSON schema. "
                f"{json_schema_error_message}"
            ),
            detail={
                "file_path": file_path,
                "json_schema_error_message": json_schema_error_message,
            },
        )


class InvalidRolePermissionsFilePermissionValueError(InvalidRolePermissionsFileError):
    """Raised when a role permissions file contains an unrecognised permission value."""

    code = "INVALID_ROLE_PERMISSIONS_FILE_PERMISSION_VALUE_ERROR"

    def __init__(self, file_path: str, role: str, permission: str):
        super().__init__(
            message=(
                f"Failed to load the role permissions file '{file_path}'. "
                f"The permission '{permission}' assigned to role '{role}' is not a "
                f"recognised UserPermissions value."
            ),
            detail={"file_path": file_path, "role": role, "permission": permission},
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
