import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

USER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string"},
        "display_name": {"type": "string"},
        "username": {"type": "string"},
        "user_account": {
            "type": "object",
            "properties": {
                "user_account_id": {"type": "string"},
                "username": {"type": "string"},
            },
            "required": ["user_account_id", "username"],
            "additionalProperties": False,
        },
        "role": {"type": "string"},
        "datetime_connected": {"type": "string"},
        "datetime_last_active": {"type": "string"},
    },
    "required": [
        "user_id",
        "display_name",
        "username",
        "role",
        "user_account",
        "datetime_connected",
        "datetime_last_active",
    ],
    "additionalProperties": False,
}
ALL_USERS_JSON_SCHEMA = {
    "type": "array",
    "items": USER_JSON_SCHEMA,
}
USER_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["USER_NOT_FOUND_ERROR"]},
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


async def test_get_own_user(client):
    validate_response(
        test_response=await client.get("/api/users/me"),
        expected_json_schema=USER_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_all_users(client):
    """All roles can GET /api/users/all."""
    validate_response(
        test_response=await client.get("/api/users/all"),
        expected_json_schema=ALL_USERS_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_user_by_user_id(admin_client, client):
    """All roles can GET /api/users/{user_id}."""
    all_users_response = await admin_client.get("/api/users/all")
    all_user_ids = [user["user_id"] for user in all_users_response.json()]

    for user_id in all_user_ids:
        validate_response(
            test_response=await client.get(f"/api/users/{user_id}"),
            expected_json_schema=USER_JSON_SCHEMA,
            expected_status_code=200,
        )
    # Non-UUID4 string: 422 (UUID validation fires before auth)
    validate_response(
        test_response=await client.get("/api/users/invalid-user-id"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )
    # Valid UUID4 that does not exist: 404
    validate_response(
        test_response=await client.get(
            "/api/users/00000000-0000-4000-8000-000000000050"
        ),
        expected_json_schema=USER_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_update_own_display_name(client):
    current_user = (await client.get("/api/users/me")).json()
    original_display_name = current_user["display_name"]

    updated = validate_response(
        test_response=await client.patch(
            "/api/users/me",
            json={"display_name": "Updated Display Name"},
        ),
        expected_json_schema=USER_JSON_SCHEMA,
        expected_status_code=200,
    )
    assert updated.json()["display_name"] == "Updated Display Name"

    validate_response(
        test_response=await client.patch(
            "/api/users/me",
            json={"display_name": original_display_name},
        ),
        expected_json_schema=USER_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_update_user_display_name_by_user_id(
    admin_client, operator_client, spectator_client, client
):
    all_users = (await admin_client.get("/api/users/all")).json()
    current_user = (await client.get("/api/users/me")).json()
    target_user = next(u for u in all_users if u["user_id"] != current_user["user_id"])
    target_user_id = target_user["user_id"]
    original_display_name = target_user["display_name"]

    if client == admin_client:
        updated = validate_response(
            test_response=await client.patch(
                f"/api/users/{target_user_id}",
                json={"display_name": "Admin Updated Name"},
            ),
            expected_json_schema=USER_JSON_SCHEMA,
            expected_status_code=200,
        )
        assert updated.json()["display_name"] == "Admin Updated Name"

        validate_response(
            test_response=await client.patch(
                f"/api/users/{target_user_id}",
                json={"display_name": original_display_name},
            ),
            expected_json_schema=USER_JSON_SCHEMA,
            expected_status_code=200,
        )

        # Non-UUID4 string: 422 (UUID validation fires before auth)
        validate_response(
            test_response=await client.patch(
                "/api/users/invalid-user-id",
                json={"display_name": "Should Fail"},
            ),
            expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )
        # Valid UUID4 that does not exist: 404
        validate_response(
            test_response=await client.patch(
                "/api/users/00000000-0000-4000-8000-000000000051",
                json={"display_name": "Should Fail"},
            ),
            expected_json_schema=USER_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.patch(
                f"/api/users/{target_user_id}",
                json={"display_name": "Should Fail"},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )
        # Non-UUID4 string: 403 (permission check fires before UUID validation)
        validate_response(
            test_response=await client.patch(
                "/api/users/invalid-user-id",
                json={"display_name": "Should Fail"},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )
        # Valid UUID4 that does not exist: 403 for low-privilege users (auth runs first)
        validate_response(
            test_response=await client.patch(
                "/api/users/00000000-0000-4000-8000-000000000051",
                json={"display_name": "Should Fail"},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )
