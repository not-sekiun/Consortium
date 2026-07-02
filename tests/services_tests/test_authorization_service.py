import json
import pathlib

import pytest

from consortium.server.exceptions.consortium_exceptions.authorization_consortium_exceptions import (
    InvalidRolePermissionsFileJSONError,
    InvalidRolePermissionsFilePermissionValueError,
    InvalidRolePermissionsFileSchemaError,
    PermissionAlreadyInRoleError,
    PermissionNotInRoleError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.services.authorization_service import AuthorizationService

_VALID_PERM = UserPermissions.READ_ALL_USERS
_VALID_PERM_2 = UserPermissions.READ_OWN_USER


@pytest.fixture
def role_permissions_file(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "role_permissions.json"
    data = {"ADMIN": [str(_VALID_PERM)], "OPERATOR": [str(_VALID_PERM_2)]}
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def service(role_permissions_file: pathlib.Path) -> AuthorizationService:
    svc = AuthorizationService(role_permissions_json_file=role_permissions_file)
    svc.load_server_role_permissions()
    return svc


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_repr(role_permissions_file: pathlib.Path):
    svc = AuthorizationService(role_permissions_json_file=role_permissions_file)
    assert "AuthorizationService" in repr(svc)


# ---------------------------------------------------------------------------
# load_role_permissions_from_path
# ---------------------------------------------------------------------------


def test_load_role_permissions_from_path_invalid_json(tmp_path: pathlib.Path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{")
    svc = AuthorizationService(role_permissions_json_file=bad)
    with pytest.raises(InvalidRolePermissionsFileJSONError):
        svc.load_role_permissions_from_path(bad)


def test_load_role_permissions_from_path_invalid_schema(tmp_path: pathlib.Path):
    # Schema requires keys to match ^[A-Z][A-Z0-9_]*$; lowercase key breaks it
    bad = tmp_path / "bad_schema.json"
    bad.write_text(json.dumps({"lowercase_key": ["READ_ALL_USERS"]}))
    svc = AuthorizationService(role_permissions_json_file=bad)
    with pytest.raises(InvalidRolePermissionsFileSchemaError):
        svc.load_role_permissions_from_path(bad)


def test_load_role_permissions_from_path_invalid_permission_value(
    tmp_path: pathlib.Path,
):
    bad = tmp_path / "bad_perm.json"
    bad.write_text(json.dumps({"ADMIN": ["NOT_A_REAL_PERMISSION"]}))
    svc = AuthorizationService(role_permissions_json_file=bad)
    with pytest.raises(InvalidRolePermissionsFilePermissionValueError):
        svc.load_role_permissions_from_path(bad)


def test_load_role_permissions_from_path_happy_path(
    role_permissions_file: pathlib.Path,
):
    svc = AuthorizationService(role_permissions_json_file=role_permissions_file)
    data = svc.load_role_permissions_from_path(role_permissions_file)
    assert "ADMIN" in data
    assert str(_VALID_PERM) in data["ADMIN"]


# ---------------------------------------------------------------------------
# save_role_permissions_to_path / save_server_role_permissions
# ---------------------------------------------------------------------------


def test_save_role_permissions_to_path_writes_file(tmp_path: pathlib.Path):
    out = tmp_path / "out.json"
    svc = AuthorizationService(role_permissions_json_file=out)
    svc.save_role_permissions_to_path(out, {"ADMIN": [str(_VALID_PERM)]})
    data = json.loads(out.read_text())
    assert data == {"ADMIN": [str(_VALID_PERM)]}


def test_save_server_role_permissions_round_trips(service: AuthorizationService):
    # Modify in memory then save; reload and check
    service.create_role("NEWROLE")
    service.save_server_role_permissions()
    path = service._role_permissions_json_file
    data = json.loads(path.read_text())
    assert "NEWROLE" in data


# ---------------------------------------------------------------------------
# get_all_roles
# ---------------------------------------------------------------------------


def test_get_all_roles_returns_copy(service: AuthorizationService):
    roles = service.get_all_roles()
    assert "ADMIN" in roles
    assert "OPERATOR" in roles
    # Verify it's a copy - mutation should not affect internal state
    roles["ADMIN"].add("FAKE_PERMISSION")
    assert "FAKE_PERMISSION" not in service.get_role_permissions("ADMIN")


# ---------------------------------------------------------------------------
# get_role_permissions
# ---------------------------------------------------------------------------


def test_get_role_permissions_returns_permissions(service: AuthorizationService):
    perms = service.get_role_permissions("ADMIN")
    assert str(_VALID_PERM) in perms


def test_get_role_permissions_not_found_raises(service: AuthorizationService):
    with pytest.raises(RoleNotFoundError):
        service.get_role_permissions("NONEXISTENT")


# ---------------------------------------------------------------------------
# create_role
# ---------------------------------------------------------------------------


def test_create_role_success(service: AuthorizationService):
    service.create_role("CUSTOM")
    assert "CUSTOM" in service.get_all_roles()


def test_create_role_with_permissions(service: AuthorizationService):
    service.create_role("CUSTOM2", permissions={str(_VALID_PERM)})
    assert str(_VALID_PERM) in service.get_role_permissions("CUSTOM2")


def test_create_role_duplicate_raises(service: AuthorizationService):
    with pytest.raises(RoleAlreadyExistsError):
        service.create_role("ADMIN")


# ---------------------------------------------------------------------------
# delete_role
# ---------------------------------------------------------------------------


def test_delete_role_success(service: AuthorizationService):
    service.create_role("TO_DELETE")
    service.delete_role("TO_DELETE")
    assert "TO_DELETE" not in service.get_all_roles()


def test_delete_role_not_found_raises(service: AuthorizationService):
    with pytest.raises(RoleNotFoundError):
        service.delete_role("NONEXISTENT")


# ---------------------------------------------------------------------------
# update_role_permissions
# ---------------------------------------------------------------------------


def test_update_role_permissions_success(service: AuthorizationService):
    service.update_role_permissions("ADMIN", {str(_VALID_PERM_2)})
    assert service.get_role_permissions("ADMIN") == {str(_VALID_PERM_2)}


def test_update_role_permissions_not_found_raises(service: AuthorizationService):
    with pytest.raises(RoleNotFoundError):
        service.update_role_permissions("NONEXISTENT", {str(_VALID_PERM)})


# ---------------------------------------------------------------------------
# add_permission_to_role
# ---------------------------------------------------------------------------


def test_add_permission_to_role_success(service: AuthorizationService):
    service.add_permission_to_role("OPERATOR", str(_VALID_PERM))
    assert str(_VALID_PERM) in service.get_role_permissions("OPERATOR")


def test_add_permission_to_role_not_found_raises(service: AuthorizationService):
    with pytest.raises(RoleNotFoundError):
        service.add_permission_to_role("NONEXISTENT", str(_VALID_PERM))


def test_add_permission_to_role_already_present_raises(service: AuthorizationService):
    with pytest.raises(PermissionAlreadyInRoleError):
        service.add_permission_to_role("ADMIN", str(_VALID_PERM))


# ---------------------------------------------------------------------------
# remove_permission_from_role
# ---------------------------------------------------------------------------


def test_remove_permission_from_role_success(service: AuthorizationService):
    service.remove_permission_from_role("ADMIN", str(_VALID_PERM))
    assert str(_VALID_PERM) not in service.get_role_permissions("ADMIN")


def test_remove_permission_from_role_not_found_raises(service: AuthorizationService):
    with pytest.raises(RoleNotFoundError):
        service.remove_permission_from_role("NONEXISTENT", str(_VALID_PERM))


def test_remove_permission_from_role_not_in_role_raises(service: AuthorizationService):
    with pytest.raises(PermissionNotInRoleError):
        service.remove_permission_from_role("ADMIN", str(_VALID_PERM_2))


# ---------------------------------------------------------------------------
# has_permission
# ---------------------------------------------------------------------------


def test_has_permission_returns_true_when_present(service: AuthorizationService):
    assert service.has_permission("ADMIN", str(_VALID_PERM)) is True


def test_has_permission_returns_false_when_absent(service: AuthorizationService):
    assert service.has_permission("ADMIN", str(_VALID_PERM_2)) is False


def test_has_permission_returns_false_for_unknown_role(service: AuthorizationService):
    # Should return False (not raise) for non-existent roles
    assert service.has_permission("NONEXISTENT_ROLE", str(_VALID_PERM)) is False
