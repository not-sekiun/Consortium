"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`AuthorizationServiceError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.AuthorizationServiceError]
        - [`InvalidRolePermissionsFileError`][consortium.server.exceptions.service_exceptions.authorization_service_exceptions.InvalidRolePermissionsFileError]
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


class InvalidRolePermissionsFileError(AuthorizationServiceError):
    """Base exception for errors when reading or writing a role permissions file."""

    code = "INVALID_ROLE_PERMISSIONS_FILE_ERROR"


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
