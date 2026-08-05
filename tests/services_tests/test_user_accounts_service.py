import json
import pathlib
import uuid

import pytest

from consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions import (
    EmptyUserAccountPasswordError,
    EmptyUserAccountUsernameError,
    InvalidUserAccountRoleError,
    UserAccountAuthenticationError,
    UserAccountIDNotFoundError,
    UserAccountsFileDuplicateUsernamesError,
    UserAccountsFileEncodingError,
    UserAccountsFileJSONError,
    UserAccountsFileSchemaError,
    UserAccountsFileSystemError,
    UserAccountUsernameAlreadyExistsError,
    UserAccountUsernameNotFoundError,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.services.authorization_service import AuthorizationService
from consortium.server.services.user_accounts_service import UserAccountsService

# A username carrying non-ASCII characters. Used to pin the explicit UTF-8 encoding on
# both the read and the write path: under a non-UTF-8 locale default this round trip
# either mojibakes the username or fails outright.
_NON_ASCII_USERNAME = "wörker"


@pytest.fixture
def role_permissions_file(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "role_permissions.json"
    path.write_text(
        json.dumps(
            {
                "ADMIN": [str(UserPermissions.READ_ALL_USER_ACCOUNTS)],
                "OPERATOR": [str(UserPermissions.READ_OWN_USER_ACCOUNT)],
                "SPECTATOR": [str(UserPermissions.READ_OWN_USER_ACCOUNT)],
            },
        ),
    )
    return path


@pytest.fixture
def authorization_service(role_permissions_file: pathlib.Path) -> AuthorizationService:
    service = AuthorizationService(role_permissions_json_file=role_permissions_file)
    service.load_server_role_permissions()
    return service


@pytest.fixture
def user_accounts_file(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "user_accounts.json"


@pytest.fixture
def service(
    user_accounts_file: pathlib.Path,
    authorization_service: AuthorizationService,
) -> UserAccountsService:
    return UserAccountsService(
        user_accounts_json_file=user_accounts_file,
        authorization_service=authorization_service,
    )


def _write_accounts_file(path: pathlib.Path, entries: list[dict]) -> pathlib.Path:
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _raise_oserror(*args, **kwargs):
    # Stands in for the residual `OSError` family (ENOSPC, EIO, a TOCTOU unlink between
    # the existence check and the open) that no pre-flight check can rule out.
    raise OSError(5, "Input/output error")


# ---------------------------------------------------------------------------
# __str__ / __repr__
# ---------------------------------------------------------------------------


def test_str_and_repr(service: UserAccountsService):
    assert str(service) == "User Accounts Service"
    assert "UserAccountsService" in repr(service)


# ---------------------------------------------------------------------------
# create_user_account
# ---------------------------------------------------------------------------


def test_create_user_account(service: UserAccountsService):
    user_account = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    assert user_account.username == "operator"
    assert user_account.password == "password"
    assert user_account.role == "OPERATOR"
    assert service.get_all_user_accounts() == [user_account]


def test_create_user_account_with_empty_username(service: UserAccountsService):
    with pytest.raises(EmptyUserAccountUsernameError):
        service.create_user_account(username="", password="password", role="OPERATOR")


def test_create_user_account_with_empty_password(service: UserAccountsService):
    with pytest.raises(EmptyUserAccountPasswordError):
        service.create_user_account(username="operator", password="", role="OPERATOR")


def test_create_user_account_with_unknown_role(service: UserAccountsService):
    with pytest.raises(InvalidUserAccountRoleError):
        service.create_user_account(
            username="operator",
            password="password",
            role="NOT_A_ROLE",
        )


def test_create_user_account_with_duplicate_username(service: UserAccountsService):
    service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    with pytest.raises(UserAccountUsernameAlreadyExistsError):
        service.create_user_account(
            username="operator",
            password="different",
            role="ADMIN",
        )


# ---------------------------------------------------------------------------
# get_user_account_by_user_account_id / get_user_account_by_username
# ---------------------------------------------------------------------------


def test_get_user_account_by_user_account_id(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    # Accepted as both a `uuid.UUID` and its string form.
    assert (
        service.get_user_account_by_user_account_id(created.user_account_id) == created
    )
    assert (
        service.get_user_account_by_user_account_id(str(created.user_account_id))
        == created
    )


def test_get_user_account_by_user_account_id_not_found(service: UserAccountsService):
    with pytest.raises(UserAccountIDNotFoundError):
        service.get_user_account_by_user_account_id(uuid.uuid4())


def test_get_user_account_by_username(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    assert service.get_user_account_by_username(username="operator") == created


def test_get_user_account_by_username_not_found(service: UserAccountsService):
    with pytest.raises(UserAccountUsernameNotFoundError):
        service.get_user_account_by_username(username="nobody")


def test_get_all_user_accounts_is_empty_by_default(service: UserAccountsService):
    assert service.get_all_user_accounts() == []


# ---------------------------------------------------------------------------
# update_user_account_by_user_account_id
# ---------------------------------------------------------------------------


def test_update_user_account_fields(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    updated = service.update_user_account_by_user_account_id(
        user_account_id=created.user_account_id,
        username="renamed",
        password="new-password",
        role="ADMIN",
    )
    assert updated.username == "renamed"
    assert updated.password == "new-password"
    assert updated.role == "ADMIN"


def test_update_user_account_leaves_none_fields_unchanged(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    updated = service.update_user_account_by_user_account_id(
        user_account_id=created.user_account_id,
        password="new-password",
    )
    assert updated.username == "operator"
    assert updated.role == "OPERATOR"
    assert updated.password == "new-password"


def test_update_user_account_not_found(service: UserAccountsService):
    with pytest.raises(UserAccountIDNotFoundError):
        service.update_user_account_by_user_account_id(
            user_account_id=uuid.uuid4(),
            username="renamed",
        )


def test_update_user_account_with_empty_username(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    with pytest.raises(EmptyUserAccountUsernameError):
        service.update_user_account_by_user_account_id(
            user_account_id=created.user_account_id,
            username="",
        )


def test_update_user_account_with_empty_password(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    with pytest.raises(EmptyUserAccountPasswordError):
        service.update_user_account_by_user_account_id(
            user_account_id=created.user_account_id,
            password="",
        )


def test_update_user_account_with_unknown_role(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    with pytest.raises(InvalidUserAccountRoleError):
        service.update_user_account_by_user_account_id(
            user_account_id=created.user_account_id,
            role="NOT_A_ROLE",
        )


def test_update_user_account_to_another_accounts_username(service: UserAccountsService):
    service.create_user_account(
        username="taken",
        password="password",
        role="OPERATOR",
    )
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    with pytest.raises(UserAccountUsernameAlreadyExistsError):
        service.update_user_account_by_user_account_id(
            user_account_id=created.user_account_id,
            username="taken",
        )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: the uniqueness scan in `update_user_account_by_user_account_id` "
        "does not exclude the account being updated, so re-submitting an account's own "
        "username raises `UserAccountUsernameAlreadyExistsError` (a 409 through "
        "`PATCH /api/user-accounts/me`) instead of being a no op. Not fixed in this "
        "pass; see the `# TODO: Check for no ops` in the service."
    ),
)
def test_update_user_account_to_its_own_username_is_a_no_op(
    service: UserAccountsService,
):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    updated = service.update_user_account_by_user_account_id(
        user_account_id=created.user_account_id,
        username="operator",
    )
    assert updated.username == "operator"


# ---------------------------------------------------------------------------
# delete_user_account_by_user_account_id
# ---------------------------------------------------------------------------


def test_delete_user_account(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    service.delete_user_account_by_user_account_id(
        user_account_id=created.user_account_id,
    )
    assert service.get_all_user_accounts() == []


def test_delete_user_account_not_found(service: UserAccountsService):
    with pytest.raises(UserAccountIDNotFoundError):
        service.delete_user_account_by_user_account_id(user_account_id=uuid.uuid4())


# ---------------------------------------------------------------------------
# authenticate_user_account_credentials
# ---------------------------------------------------------------------------


def test_authenticate_user_account_credentials(service: UserAccountsService):
    created = service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    authenticated = service.authenticate_user_account_credentials(
        username="operator",
        password="password",
    )
    assert authenticated == created


def test_authenticate_user_account_credentials_wrong_password(
    service: UserAccountsService,
):
    service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    with pytest.raises(UserAccountAuthenticationError):
        service.authenticate_user_account_credentials(
            username="operator",
            password="wrong",
        )


def test_authenticate_user_account_credentials_unknown_username(
    service: UserAccountsService,
):
    with pytest.raises(UserAccountAuthenticationError):
        service.authenticate_user_account_credentials(
            username="nobody",
            password="password",
        )


# ---------------------------------------------------------------------------
# read_user_accounts_from_user_accounts_file: path level failures
# ---------------------------------------------------------------------------


def test_read_user_accounts_file_not_found(
    service: UserAccountsService,
    tmp_path: pathlib.Path,
):
    # Left to `open()` rather than pre-checked, so this asserts the wrapping works.
    with pytest.raises(UserAccountsFileSystemError) as exc_info:
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=tmp_path / "missing.json",
        )
    assert "FileNotFoundError" in exc_info.value.detail["underlying_error"]


def test_read_user_accounts_filepath_is_directory(
    service: UserAccountsService,
    tmp_path: pathlib.Path,
):
    # Pre-checked rather than left to `open()`, because Windows reports opening a
    # directory as `PermissionError`, which names the wrong problem. The message has to
    # say it is a directory whatever the platform.
    directory = tmp_path / "accounts_dir"
    directory.mkdir()
    with pytest.raises(UserAccountsFileSystemError) as exc_info:
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=directory,
        )
    assert "directory" in exc_info.value.message


def test_read_user_accounts_wraps_oserror(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _write_accounts_file(user_accounts_file, [])
    monkeypatch.setattr(pathlib.Path, "open", _raise_oserror)
    with pytest.raises(UserAccountsFileSystemError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_read_user_accounts_wraps_permission_error(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    # `PermissionError` used to have its own `UserAccountsFileReadAccessError`. It is now
    # folded into the single filesystem error alongside the rest of the `OSError` family.
    def _raise_permission_error(*args, **kwargs):
        raise PermissionError(13, "Permission denied")

    _write_accounts_file(user_accounts_file, [])
    monkeypatch.setattr(pathlib.Path, "open", _raise_permission_error)
    with pytest.raises(UserAccountsFileSystemError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_read_user_accounts_undecodable_bytes(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    # Pinning `encoding="utf-8"` removes the locale-drift cause of a decode failure but
    # not this one: the bytes on disk are simply not valid UTF-8. Reported as a defect in
    # the file's contents rather than as a filesystem fault.
    user_accounts_file.write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(UserAccountsFileEncodingError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


# ---------------------------------------------------------------------------
# read_user_accounts_from_user_accounts_file: content level failures
# ---------------------------------------------------------------------------


def test_read_user_accounts_invalid_json(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    user_accounts_file.write_text("not json {{", encoding="utf-8")
    with pytest.raises(UserAccountsFileJSONError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_read_user_accounts_top_level_is_not_a_list(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    user_accounts_file.write_text(
        json.dumps({"username": "operator"}), encoding="utf-8"
    )
    with pytest.raises(UserAccountsFileSchemaError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_read_user_accounts_missing_required_field(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    # The JSON schema this replaced declared `properties` without `required`, so an entry
    # missing `password` passed schema validation and then escaped as a raw
    # `pydantic.ValidationError` from the model construction below it.
    _write_accounts_file(
        user_accounts_file,
        [{"username": "operator", "role": "OPERATOR"}],
    )
    with pytest.raises(UserAccountsFileSchemaError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


@pytest.mark.parametrize("field", ["username", "password"])
def test_read_user_accounts_empty_field(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
    field: str,
):
    entry = {"username": "operator", "password": "password", "role": "OPERATOR"}
    entry[field] = ""
    _write_accounts_file(user_accounts_file, [entry])
    with pytest.raises(UserAccountsFileSchemaError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_read_user_accounts_rejects_unknown_fields(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    _write_accounts_file(
        user_accounts_file,
        [
            {
                "username": "operator",
                "password": "password",
                "role": "OPERATOR",
                "unexpected": "value",
            },
        ],
    )
    with pytest.raises(UserAccountsFileSchemaError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_read_user_accounts_unknown_role(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    # Roles are checked against the authorization service rather than a hardcoded enum,
    # so a role absent from the loaded role permissions is rejected here.
    _write_accounts_file(
        user_accounts_file,
        [{"username": "operator", "password": "password", "role": "NOT_A_ROLE"}],
    )
    with pytest.raises(InvalidUserAccountRoleError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_read_user_accounts_conflicts_with_registered_account(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    _write_accounts_file(
        user_accounts_file,
        [{"username": "operator", "password": "other", "role": "ADMIN"}],
    )
    with pytest.raises(UserAccountUsernameAlreadyExistsError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "HIGH_DIFF.md H4: `new_usernames` is never appended to, so the in-file duplicate "
        "check is unreachable and both entries load as separate accounts sharing a "
        "username. Deferred: the fix changes whether a server that boots today keeps "
        "booting."
    ),
)
def test_read_user_accounts_duplicate_usernames_within_file(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    _write_accounts_file(
        user_accounts_file,
        [
            {"username": "operator", "password": "first", "role": "OPERATOR"},
            {"username": "operator", "password": "second", "role": "ADMIN"},
        ],
    )
    with pytest.raises(UserAccountsFileDuplicateUsernamesError):
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


# ---------------------------------------------------------------------------
# read_user_accounts_from_user_accounts_file: happy paths
# ---------------------------------------------------------------------------


def test_read_user_accounts_does_not_register_them(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    _write_accounts_file(
        user_accounts_file,
        [{"username": "operator", "password": "password", "role": "OPERATOR"}],
    )
    read_user_accounts = service.read_user_accounts_from_user_accounts_file(
        user_accounts_filepath=user_accounts_file,
    )
    assert len(read_user_accounts) == 1
    assert read_user_accounts[0].username == "operator"
    assert service.get_all_user_accounts() == []


def test_read_user_accounts_empty_file(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    _write_accounts_file(user_accounts_file, [])
    assert (
        service.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )
        == []
    )


def test_read_user_accounts_decodes_utf8_regardless_of_locale(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    user_accounts_file.write_bytes(
        json.dumps(
            [
                {
                    "username": _NON_ASCII_USERNAME,
                    "password": "password",
                    "role": "OPERATOR",
                },
            ],
            ensure_ascii=False,
        ).encode("utf-8"),
    )
    read_user_accounts = service.read_user_accounts_from_user_accounts_file(
        user_accounts_filepath=user_accounts_file,
    )
    assert read_user_accounts[0].username == _NON_ASCII_USERNAME


# ---------------------------------------------------------------------------
# load_user_accounts_from_user_accounts_file
# ---------------------------------------------------------------------------


def test_load_user_accounts_registers_them(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    _write_accounts_file(
        user_accounts_file,
        [
            {"username": "operator", "password": "password", "role": "OPERATOR"},
            {"username": "admin", "password": "password", "role": "ADMIN"},
        ],
    )
    loaded = service.load_user_accounts_from_user_accounts_file(
        user_accounts_filepath=user_accounts_file,
    )
    assert len(loaded) == 2
    assert {u.username for u in service.get_all_user_accounts()} == {
        "operator",
        "admin",
    }


def test_load_user_accounts_propagates_read_errors(
    service: UserAccountsService,
    tmp_path: pathlib.Path,
):
    with pytest.raises(UserAccountsFileSystemError):
        service.load_user_accounts_from_user_accounts_file(
            user_accounts_filepath=tmp_path / "missing.json",
        )


# ---------------------------------------------------------------------------
# write_user_accounts_to_user_accounts_file
# ---------------------------------------------------------------------------


def test_write_user_accounts_round_trips(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    bytes_written = service.write_user_accounts_to_user_accounts_file(
        user_accounts_filepath=user_accounts_file,
    )
    # The reported count is bytes, so it has to match the file's actual size. A text mode
    # write would report characters and under-report by one byte per newline on any
    # platform that translates them.
    assert bytes_written == user_accounts_file.stat().st_size

    written = json.loads(user_accounts_file.read_text(encoding="utf-8"))
    assert written == [
        {"username": "operator", "password": "password", "role": "OPERATOR"},
    ]


def test_write_user_accounts_does_not_translate_newlines(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    # Written as bytes, so the file is byte identical whatever host produced it.
    service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    service.write_user_accounts_to_user_accounts_file(
        user_accounts_filepath=user_accounts_file,
    )
    raw = user_accounts_file.read_bytes()
    assert b"\n" in raw
    assert b"\r\n" not in raw


def test_write_user_accounts_encodes_utf8_regardless_of_locale(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
    authorization_service: AuthorizationService,
):
    service.create_user_account(
        username=_NON_ASCII_USERNAME,
        password="password",
        role="OPERATOR",
    )
    service.write_user_accounts_to_user_accounts_file(
        user_accounts_filepath=user_accounts_file,
    )
    assert (
        json.loads(user_accounts_file.read_bytes().decode("utf-8"))[0]["username"]
        == _NON_ASCII_USERNAME
    )

    # Read back through a second service so both halves of the round trip agree on UTF-8.
    # It has to be a separate instance: reading into the service that already holds the
    # account would (correctly) fail the conflict check against the registered username.
    reader = UserAccountsService(
        user_accounts_json_file=user_accounts_file,
        authorization_service=authorization_service,
    )
    read_user_accounts = reader.read_user_accounts_from_user_accounts_file(
        user_accounts_filepath=user_accounts_file,
    )
    assert read_user_accounts[0].username == _NON_ASCII_USERNAME


def test_write_user_accounts_filepath_is_directory(
    service: UserAccountsService,
    tmp_path: pathlib.Path,
):
    directory = tmp_path / "accounts_dir"
    directory.mkdir()
    with pytest.raises(UserAccountsFileSystemError) as exc_info:
        service.write_user_accounts_to_user_accounts_file(
            user_accounts_filepath=directory,
        )
    assert "directory" in exc_info.value.message


def test_write_user_accounts_wraps_oserror(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(pathlib.Path, "open", _raise_oserror)
    with pytest.raises(UserAccountsFileSystemError):
        service.write_user_accounts_to_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_write_user_accounts_wraps_permission_error(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    def _raise_permission_error(*args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(pathlib.Path, "open", _raise_permission_error)
    with pytest.raises(UserAccountsFileSystemError):
        service.write_user_accounts_to_user_accounts_file(
            user_accounts_filepath=user_accounts_file,
        )


def test_write_user_accounts_escapes_unencodable_username(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    # `json.loads` accepts an unpaired surrogate escape, so a username that no UTF-8
    # encoder would accept back can reach the registry. It still writes, because
    # `json.dumps` defaults to `ensure_ascii=True` and escapes it before the encoder ever
    # sees it. This is why the write path has no encoding error counterpart to the read
    # path's, and it fails if anyone passes `ensure_ascii=False`.
    service.create_user_account(
        username="bad\ud800name",
        password="password",
        role="OPERATOR",
    )
    bytes_written = service.write_user_accounts_to_user_accounts_file(
        user_accounts_filepath=user_accounts_file,
    )
    assert bytes_written == user_accounts_file.stat().st_size
    assert user_accounts_file.read_bytes().decode("ascii").count("\\ud800") == 1


# ---------------------------------------------------------------------------
# load_framework_user_accounts / reload_framework_user_accounts /
# write_framework_user_accounts
# ---------------------------------------------------------------------------


def test_load_framework_user_accounts(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    _write_accounts_file(
        user_accounts_file,
        [{"username": "operator", "password": "password", "role": "OPERATOR"}],
    )
    assert service.load_framework_user_accounts() is True
    assert len(service.get_all_user_accounts()) == 1


def test_load_framework_user_accounts_returns_false_on_service_error(
    service: UserAccountsService,
):
    # The accounts file was never created by the fixture, so the load fails.
    assert service.load_framework_user_accounts() is False
    assert service.get_all_user_accounts() == []


def test_load_framework_user_accounts_returns_false_on_filesystem_error(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    # Pins the behaviour change from folding the raw `OSError` family into a
    # `UserAccountsServiceError` subclass: what used to propagate out of this method now
    # gets caught and reported as `False`. Unlike the write path, loading still reports
    # through its return value, and `server.py` still discards it, so a server whose
    # accounts file cannot be read boots with zero accounts and nobody able to log in.
    _write_accounts_file(user_accounts_file, [])
    monkeypatch.setattr(pathlib.Path, "open", _raise_oserror)
    assert service.load_framework_user_accounts() is False


def test_reload_framework_user_accounts_replaces_existing_accounts(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    service.create_user_account(
        username="stale",
        password="password",
        role="OPERATOR",
    )
    _write_accounts_file(
        user_accounts_file,
        [{"username": "operator", "password": "password", "role": "OPERATOR"}],
    )
    assert service.reload_framework_user_accounts() is True
    assert [u.username for u in service.get_all_user_accounts()] == ["operator"]


def test_reload_framework_user_accounts_returns_false_on_service_error(
    service: UserAccountsService,
):
    assert service.reload_framework_user_accounts() is False


def test_write_framework_user_accounts(
    service: UserAccountsService,
    user_accounts_file: pathlib.Path,
):
    service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    assert service.write_framework_user_accounts() == user_accounts_file.stat().st_size


def test_write_framework_user_accounts_propagates_filesystem_error(
    service: UserAccountsService,
    monkeypatch: pytest.MonkeyPatch,
):
    # A failed write means the registry and the file have diverged, so it propagates
    # instead of being reported as a return value nobody reads. This is what revives the
    # `except UserAccountsFileError -> InternalServerError` handlers in the user accounts
    # API, which were unreachable while this method swallowed and returned `False`.
    service.create_user_account(
        username="operator",
        password="password",
        role="OPERATOR",
    )
    monkeypatch.setattr(pathlib.Path, "open", _raise_oserror)
    with pytest.raises(UserAccountsFileSystemError):
        service.write_framework_user_accounts()
