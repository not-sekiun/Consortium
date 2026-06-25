import uuid

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
    SUCCESS_JSON_SCHEMA,
)
from tests.api_tests.utils import get_all_user_account_ids, validate_response

pytestmark = pytest.mark.anyio

USER_ACCOUNT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "user_account_id": {"type": "string"},
        "username": {"type": "string"},
        "password": {"type": "string"},
        "role": {"type": "string", "enum": ["ADMIN", "OPERATOR", "SPECTATOR"]},
    },
    "required": ["user_account_id", "username", "password", "role"],
    "additionalProperties": False,
}
ALL_USER_ACCOUNTS_JSON_SCHEMA = {
    "type": "array",
    "items": USER_ACCOUNT_JSON_SCHEMA,
}
USER_ACCOUNT_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["USER_ACCOUNT_NOT_FOUND_ERROR"]},
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
USER_ACCOUNT_AUTHENTICATION_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["USER_ACCOUNT_AUTHENTICATION_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
@pytest.mark.parametrize(
    "test_user_account",
    [
        (uuid.uuid4().hex, uuid.uuid4().hex, "ADMIN"),
        (uuid.uuid4().hex, uuid.uuid4().hex, "OPERATOR"),
        (uuid.uuid4().hex, uuid.uuid4().hex, "SPECTATOR"),
    ],
)
async def test_create_user_account(admin_client, client, test_user_account):
    if client == admin_client:
        user_account = validate_response(
            test_response=await admin_client.post(
                "/api/user-accounts",
                json={
                    "username": test_user_account[0],
                    "password": test_user_account[1],
                    "role": test_user_account[2],
                },
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=201,
        ).json()
        validate_response(
            test_response=await admin_client.get(
                f"/api/user-accounts/{user_account['user_account_id']}",
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda r, u=test_user_account: (
                r.json()["username"] == u[0]
                and r.json()["password"] == u[1]
                and r.json()["role"] == u[2]
            ),
        )
    else:
        validate_response(
            test_response=await client.post(
                "/api/user-accounts",
                json={
                    "username": test_user_account[0],
                    "password": test_user_account[1],
                    "role": test_user_account[2],
                },
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_create_user_account_with_duplicate_username(admin_client, client):
    """Duplicate username returns 409 with USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR."""
    if client == admin_client:
        validate_response(
            test_response=await admin_client.post(
                "/api/user-accounts",
                json={"username": "admin", "password": "somepass", "role": "OPERATOR"},
            ),
            expected_json_schema=USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )


async def test_get_own_user_account(client):
    validate_response(
        test_response=await client.get("/api/user-accounts/me"),
        expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_user_account_by_user_account_id(admin_client, client):
    all_ids = await get_all_user_account_ids(admin_client)
    if client == admin_client:
        for ua_id in all_ids:
            validate_response(
                test_response=await client.get(f"/api/user-accounts/{ua_id}"),
                expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
                expected_status_code=200,
            )
        # Non-UUID4 string: 422
        validate_response(
            test_response=await client.get("/api/user-accounts/not-a-valid-uuid"),
            expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )
        # Valid UUID4 that does not exist: 404
        validate_response(
            test_response=await client.get(
                "/api/user-accounts/00000000-0000-4000-8000-000000000070"
            ),
            expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        for ua_id in all_ids:
            validate_response(
                test_response=await client.get(f"/api/user-accounts/{ua_id}"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
        # Non-UUID4 string: 403 (auth fires before UUID validation)
        validate_response(
            test_response=await client.get("/api/user-accounts/not-a-valid-uuid"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_get_all_user_accounts(admin_client, client):
    if client == admin_client:
        validate_response(
            test_response=await client.get("/api/user-accounts/all"),
            expected_json_schema=ALL_USER_ACCOUNTS_JSON_SCHEMA,
            expected_status_code=200,
        )
    else:
        validate_response(
            test_response=await client.get("/api/user-accounts/all"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_update_user_account_username_by_user_account_id(admin_client, client):
    new_username = uuid.uuid4().hex
    user = (await client.get("/api/users/me")).json()
    user_account_id = user["user_account"]["user_account_id"]

    if client == admin_client:
        validate_response(
            test_response=await client.patch(
                f"/api/user-accounts/{user_account_id}",
                json={"username": new_username},
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda r: r.json()["username"] == new_username,
        )
    else:
        validate_response(
            test_response=await client.patch(
                f"/api/user-accounts/{user_account_id}",
                json={"username": new_username},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_update_user_account_password_by_user_account_id(admin_client, client):
    user_account = (await client.get("/api/user-accounts/me")).json()
    user_account_id = user_account["user_account_id"]
    new_password = uuid.uuid4().hex

    if client == admin_client:
        validate_response(
            test_response=await client.patch(
                f"/api/user-accounts/{user_account_id}",
                json={"password": new_password},
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda r: r.json()["password"] == new_password,
        )
    else:
        validate_response(
            test_response=await client.patch(
                f"/api/user-accounts/{user_account_id}",
                json={"password": new_password},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_update_user_account_role_by_user_account_id(admin_client, client):
    old_to_new_role = {"ADMIN": "ADMIN", "OPERATOR": "SPECTATOR", "SPECTATOR": "ADMIN"}
    user_account = (await client.get("/api/user-accounts/me")).json()
    user_account_id = user_account["user_account_id"]
    new_role = old_to_new_role[user_account["role"]]

    if client == admin_client:
        validate_response(
            test_response=await client.patch(
                f"/api/user-accounts/{user_account_id}",
                json={"role": new_role},
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda r: r.json()["role"] == new_role,
        )
    else:
        validate_response(
            test_response=await client.patch(
                f"/api/user-accounts/{user_account_id}",
                json={"role": new_role},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_update_user_account_by_user_account_id(admin_client, client):
    old_to_new_role = {"ADMIN": "ADMIN", "OPERATOR": "SPECTATOR", "SPECTATOR": "ADMIN"}

    if client == admin_client:
        all_ids = await get_all_user_account_ids(admin_client)
        for ua_id in all_ids:
            ua = (await admin_client.get(f"/api/user-accounts/{ua_id}")).json()
            new_username = uuid.uuid4().hex
            new_password = uuid.uuid4().hex
            new_role = old_to_new_role[ua["role"]]
            validate_response(
                test_response=await admin_client.patch(
                    f"/api/user-accounts/{ua_id}",
                    json={
                        "username": new_username,
                        "password": new_password,
                        "role": new_role,
                    },
                ),
                expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
                expected_status_code=200,
                validator_function=lambda r,
                u=new_username,
                p=new_password,
                ro=new_role: (
                    r.json()["username"] == u
                    and r.json()["password"] == p
                    and r.json()["role"] == ro
                ),
            )
    else:
        all_ids = await get_all_user_account_ids(admin_client)
        for ua_id in all_ids:
            validate_response(
                test_response=await client.patch(
                    f"/api/user-accounts/{ua_id}",
                    json={
                        "username": uuid.uuid4().hex,
                        "password": uuid.uuid4().hex,
                        "role": "OPERATOR",
                    },
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_update_user_account_by_user_account_id_not_found(admin_client):
    """Patching a non-existent (valid UUID4) user account returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000000"
    validate_response(
        test_response=await admin_client.patch(
            f"/api/user-accounts/{fake_uuid}",
            json={"username": "newname"},
        ),
        expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_update_user_account_by_invalid_uuid_returns_422(admin_client):
    """PATCH /api/user-accounts/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.patch(
            "/api/user-accounts/not-a-valid-uuid",
            json={"username": "newname"},
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_update_own_user_account(admin_client, operator_client, client):
    """PATCH /api/user-accounts/me — admins and operators can update own account."""
    new_username = uuid.uuid4().hex

    if client in (admin_client, operator_client):
        user_account = (await client.get("/api/user-accounts/me")).json()
        old_password = user_account["password"]

        validate_response(
            test_response=await client.patch(
                "/api/user-accounts/me",
                json={
                    "username": new_username,
                    "password": {
                        "old_password": old_password,
                        "new_password": uuid.uuid4().hex,
                    },
                },
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda r: r.json()["username"] == new_username,
        )
    else:
        # Spectators do not have UPDATE_OWN_USER_ACCOUNT permission
        validate_response(
            test_response=await client.patch(
                "/api/user-accounts/me",
                json={"username": new_username},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_update_own_user_account_wrong_old_password(admin_client):
    """Wrong old_password on PATCH /api/user-accounts/me returns 403."""
    validate_response(
        test_response=await admin_client.patch(
            "/api/user-accounts/me",
            json={
                "password": {
                    "old_password": "definitely-wrong-password",
                    "new_password": "newpassword",
                }
            },
        ),
        expected_json_schema=USER_ACCOUNT_AUTHENTICATION_ERROR_JSON_SCHEMA,
        expected_status_code=403,
    )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_delete_user_account_by_user_account_id(admin_client, client):
    if client == admin_client:
        all_ids = await get_all_user_account_ids(admin_client)
        for ua_id in all_ids:
            validate_response(
                test_response=await client.delete(f"/api/user-accounts/{ua_id}"),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
            validate_response(
                test_response=await client.get(f"/api/user-accounts/{ua_id}"),
                expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_JSON_SCHEMA,
                expected_status_code=404,
            )
    else:
        all_ids = await get_all_user_account_ids(admin_client)
        for ua_id in all_ids:
            validate_response(
                test_response=await client.delete(f"/api/user-accounts/{ua_id}"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
async def test_delete_user_account_not_found(admin_client):
    """Deleting a non-existent (valid UUID4) user account returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000001"
    validate_response(
        test_response=await admin_client.delete(f"/api/user-accounts/{fake_uuid}"),
        expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_user_account_by_invalid_uuid_returns_422(admin_client):
    """DELETE /api/user-accounts/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.delete("/api/user-accounts/not-a-valid-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )
