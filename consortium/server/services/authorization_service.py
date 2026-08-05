import json
import pathlib

import jsonschema
from loguru import logger

from consortium.server.exceptions.service_exceptions.authorization_service_exceptions import (
    InvalidRolePermissionsFileEncodingError,
    InvalidRolePermissionsFileJSONError,
    InvalidRolePermissionsFilePermissionValueError,
    InvalidRolePermissionsFileSchemaError,
    PermissionAlreadyInRoleError,
    PermissionNotInRoleError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
    RolePermissionsFileSystemError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.utils import wrap_filesystem_errors


class AuthorizationService:
    _ROLE_PERMISSIONS_JSON_SCHEMA = {
        "type": "object",
        "patternProperties": {
            "^[A-Z][A-Z0-9_]*$": {
                "type": "array",
                "items": {"type": "string"},
                "uniqueItems": True,
            }
        },
        "additionalProperties": False,
    }

    def __init__(self, role_permissions_json_file: pathlib.Path):
        self._role_permissions_json_file = role_permissions_json_file
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        # Mapping of role name -> set of permission strings
        self._role_permissions: dict[str, set[str]] = {}
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Authorization Service"

    def __repr__(self) -> str:
        return (
            f"AuthorizationService("
            f"role_permissions_json_file={self._role_permissions_json_file!r}"
            ")"
        )

    def load_role_permissions_from_path(
        self, path: pathlib.Path
    ) -> dict[str, list[str]]:
        """Reads, validates and returns role permission data from *path*.

        The file must contain a JSON object whose keys are role name strings
        (uppercase letters, digits, and underscores) and whose values are arrays
        of UserPermissions string values.

        Args:
            path: Absolute path to the role permissions JSON file to load.

        Returns:
            The validated role-to-permissions mapping.

        Raises:
            RolePermissionsFileSystemError: If `path` cannot be opened or read, for
                example it does not exist, read permission is denied, or the path
                points to a directory.
            InvalidRolePermissionsFileEncodingError: If the file's contents cannot
                be decoded as UTF-8 text.
            InvalidRolePermissionsFileJSONError: If the file is not valid JSON.
            InvalidRolePermissionsFileSchemaError: If the file does not conform
                to the expected JSON schema.
            InvalidRolePermissionsFilePermissionValueError: If any permission
                string is not a recognised UserPermissions value.
        """
        valid_permissions = {p.value for p in UserPermissions}
        with wrap_filesystem_errors(
            RolePermissionsFileSystemError,
            operation="read the role permissions file",
            path=path,
        ):
            try:
                # The encoding is pinned rather than left to the platform default, so a
                # file written as UTF-8 reads back identically everywhere. Without it,
                # bytes that are not valid UTF-8 are silently decoded as whatever the
                # locale encoding happens to be (cp1252 on Windows) and surface later as
                # a confusing JSON parse failure rather than as an encoding problem.
                with path.open(mode="r", encoding="utf-8") as file:
                    data: dict[str, list[str]] = json.load(file)
            except UnicodeDecodeError as exc:
                raise InvalidRolePermissionsFileEncodingError(
                    file_path=str(path),
                    underlying_error=f"{type(exc).__name__}: {exc}",
                ) from None
            except json.JSONDecodeError:
                raise InvalidRolePermissionsFileJSONError(file_path=str(path)) from None
        try:
            jsonschema.validate(data, self._ROLE_PERMISSIONS_JSON_SCHEMA)
        except jsonschema.ValidationError as exc:
            raise InvalidRolePermissionsFileSchemaError(
                file_path=str(path),
                json_schema_error_message=str(exc),
            ) from None
        for role, permissions in data.items():
            for permission in permissions:
                if permission not in valid_permissions:
                    raise InvalidRolePermissionsFilePermissionValueError(
                        file_path=str(path),
                        role=role,
                        permission=permission,
                    )
        self._logger.debug(
            "Loaded role permissions from '{}' ({} role(s))", path, len(data)
        )
        return data

    def save_role_permissions_to_path(
        self, path: pathlib.Path, role_permissions: dict[str, list[str]]
    ) -> None:
        """Serialises *role_permissions* to JSON and writes it to *path*.

        Args:
            path: Absolute path to write the role permissions JSON file to.
            role_permissions: Mapping of role name -> list of permission strings
                to persist.

        Raises:
            RolePermissionsFileSystemError: If `path` cannot be opened or written to,
                for example the parent directory does not exist, write permission is
                denied, or the disk is full.
        """
        # `role_permissions` is built by this service at `save_server_role_permissions`
        # as `dict[str, sorted(set[str])]`, which is unconditionally JSON serialisable
        # and cannot contain a circular reference, so `json.dumps` cannot fail here.
        data = json.dumps(role_permissions, indent=4)
        with wrap_filesystem_errors(
            RolePermissionsFileSystemError,
            operation="write the role permissions file",
            path=path,
        ):
            with path.open(mode="w", encoding="utf-8") as file:
                file.write(data)
        self._logger.debug(
            "Saved role permissions to '{}' ({} byte(s) written)",
            path,
            len(data),
        )

    def load_server_role_permissions(self) -> None:
        """Loads role permissions from the server's default role_permissions.json file.

        Calls `load_role_permissions_from_path` with the path supplied at
        construction time and replaces the current in-memory role permissions
        with the loaded data.

        Raises:
            RolePermissionsFileSystemError: Propagated from the base loader.
            InvalidRolePermissionsFileEncodingError: Propagated from the base loader.
            InvalidRolePermissionsFileJSONError: Propagated from the base loader.
            InvalidRolePermissionsFileSchemaError: Propagated from the base loader.
            InvalidRolePermissionsFilePermissionValueError: Propagated from the
                base loader.
        """
        data = self.load_role_permissions_from_path(self._role_permissions_json_file)
        self._role_permissions = {
            role: set(permissions) for role, permissions in data.items()
        }
        self._logger.debug(
            "Loaded server role permissions ({} role(s) loaded)",
            len(self._role_permissions),
        )

    def save_server_role_permissions(self) -> None:
        """Persists the current in-memory role permissions to the server's default file.

        Calls `save_role_permissions_to_path` with the path supplied at
        construction time and the current in-memory state.

        Raises:
            RolePermissionsFileSystemError: Propagated from the base writer.
        """
        serialisable = {
            role: sorted(permissions)
            for role, permissions in self._role_permissions.items()
        }
        self.save_role_permissions_to_path(
            self._role_permissions_json_file, serialisable
        )
        self._logger.debug(
            "Saved server role permissions to '{}'",
            self._role_permissions_json_file,
        )

    def get_all_roles(self) -> dict[str, set[str]]:
        """Returns a copy of the current role-to-permissions mapping.

        Returns:
            Mapping of role name -> set of permission strings.
        """
        return {
            role: set(permissions)
            for role, permissions in self._role_permissions.items()
        }

    def get_role_permissions(self, role: str) -> set[str]:
        """Returns the set of permissions assigned to *role*.

        Args:
            role: The name of the role to look up.

        Returns:
            The permissions assigned to the role.

        Raises:
            RoleNotFoundError: If no role with the given name exists.
        """
        try:
            return set(self._role_permissions[role])
        except KeyError:
            raise RoleNotFoundError(role=role) from None

    def create_role(self, role: str, permissions: set[str] | None = None) -> None:
        """Creates a new role with an optional initial set of permissions.

        Args:
            role: The name of the new role. No format validation is performed
                here, any string is accepted. Note that
                `_ROLE_PERMISSIONS_JSON_SCHEMA` requires role names to match
                ``^[A-Z][A-Z0-9_]*$`` when a role permissions file is loaded
                (see `load_role_permissions_from_path`), so a role created here
                whose name violates that pattern will fail to load back the
                next time `load_server_role_permissions` is called.
            permissions: Initial permissions to assign. When ``None``, the role
                starts with no permissions.

        Raises:
            RoleAlreadyExistsError: If a role with the given name already exists.
        """
        if role in self._role_permissions:
            raise RoleAlreadyExistsError(role=role)
        self._role_permissions[role] = set(permissions) if permissions else set()
        self._logger.debug("Created role '{}'", role)

    def delete_role(self, role: str) -> None:
        """Removes the specified role and all of its permissions.

        Args:
            role: The name of the role to delete.

        Raises:
            RoleNotFoundError: If no role with the given name exists.
        """
        if role not in self._role_permissions:
            raise RoleNotFoundError(role=role)
        del self._role_permissions[role]
        self._logger.debug("Deleted role '{}'", role)

    def update_role_permissions(self, role: str, permissions: set[str]) -> None:
        """Replaces all permissions for *role* with *permissions*.

        Args:
            role: The name of the role to update.
            permissions: The complete new set of permissions for the role.

        Raises:
            RoleNotFoundError: If no role with the given name exists.
        """
        if role not in self._role_permissions:
            raise RoleNotFoundError(role=role)
        self._role_permissions[role] = set(permissions)
        self._logger.debug(
            "Updated permissions for role '{}' ({} permission(s))",
            role,
            len(permissions),
        )

    def add_permission_to_role(self, role: str, permission: str) -> None:
        """Adds a single permission to an existing role.

        Args:
            role: The name of the role to modify.
            permission: The permission string to add.

        Raises:
            RoleNotFoundError: If no role with the given name exists.
            PermissionAlreadyInRoleError: If the permission is already assigned
                to the role.
        """
        if role not in self._role_permissions:
            raise RoleNotFoundError(role=role)
        if permission in self._role_permissions[role]:
            raise PermissionAlreadyInRoleError(role=role, permission=permission)
        self._role_permissions[role].add(permission)
        self._logger.debug("Added permission '{}' to role '{}'", permission, role)

    def remove_permission_from_role(self, role: str, permission: str) -> None:
        """Removes a single permission from an existing role.

        Args:
            role: The name of the role to modify.
            permission: The permission string to remove.

        Raises:
            RoleNotFoundError: If no role with the given name exists.
            PermissionNotInRoleError: If the permission is not assigned to the role.
        """
        if role not in self._role_permissions:
            raise RoleNotFoundError(role=role)
        if permission not in self._role_permissions[role]:
            raise PermissionNotInRoleError(role=role, permission=permission)
        self._role_permissions[role].discard(permission)
        self._logger.debug("Removed permission '{}' from role '{}'", permission, role)

    def has_permission(self, role: str, permission: str) -> bool:
        """Returns whether a role has a particular permission.

        Returns `False` (rather than raising) when the role does not exist, to
        keep the FastAPI dependency path simple.

        Args:
            role: The role name to check (accepts raw strings and StrEnum values).
            permission: The permission string to test for.

        Returns:
            `True` if the role exists and holds the permission.
        """
        permissions = self._role_permissions.get(str(role))
        if permissions is None:
            return False
        return str(permission) in permissions
