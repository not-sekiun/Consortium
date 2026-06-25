import httpx
import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
    SUCCESS_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


async def test_logout_from_server(app, admin_client, operator_client, spectator_client):
    """All roles can logout themselves, after which their token becomes invalid."""
    sessions_with_credentials = [
        (admin_client, "admin", "admin"),
        (operator_client, "operator", "operator"),
        (spectator_client, "spectator", "spectator"),
    ]
    for session, username, password in sessions_with_credentials:
        validate_response(
            test_response=await session.post("/api/logout"),
            expected_json_schema=SUCCESS_JSON_SCHEMA,
            expected_status_code=200,
        )
        validate_response(
            test_response=await session.get("/api/users/me"),
            expected_status_code=401,
        )
        # Re-login so subsequent tests can still use this session
        response = await session.post(
            "/api/login",
            data={"username": username, "password": password},
        )
        assert response.status_code == 200, f"Re-login failed for {username}"
        session.headers["Authorization"] = f"Bearer {response.json()['access_token']}"


async def test_logout_user_by_user_id(
    app, admin_client, operator_client, spectator_client
):
    """Admin can force-logout a user by user_id; non-admins get 403."""
    second_admin = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )
    try:
        login_resp = await second_admin.post(
            "/api/login",
            data={"username": "admin", "password": "admin"},
        )
        assert login_resp.status_code == 200
        second_admin.headers["Authorization"] = (
            f"Bearer {login_resp.json()['access_token']}"
        )

        target_user_id = (await second_admin.get("/api/users/me")).json()["user_id"]

        validate_response(
            test_response=await second_admin.get("/api/users/me"),
            expected_status_code=200,
        )

        validate_response(
            test_response=await admin_client.post(f"/api/logout/user/{target_user_id}"),
            expected_json_schema=SUCCESS_JSON_SCHEMA,
            expected_status_code=200,
        )

        validate_response(
            test_response=await second_admin.get("/api/users/me"),
            expected_status_code=401,
        )

        # Non-UUID string: 422 (UUID validation fires before lookup for admin)
        validate_response(
            test_response=await admin_client.post("/api/logout/user/invalid-user-id"),
            expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )

        # Operator and spectator get 403; 403 fires before UUID validation for non-admins
        for non_admin in [operator_client, spectator_client]:
            validate_response(
                test_response=await non_admin.post(
                    f"/api/logout/user/{target_user_id}"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            validate_response(
                test_response=await non_admin.post("/api/logout/user/invalid-user-id"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
    finally:
        await second_admin.aclose()


async def test_logout_user_account_by_user_account_id(
    app, admin_client, operator_client, spectator_client
):
    """Admin can force-logout all sessions for a user account by user_account_id."""
    second_spectator = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )
    try:
        login_resp = await second_spectator.post(
            "/api/login",
            data={"username": "spectator", "password": "spectator"},
        )
        assert login_resp.status_code == 200
        second_spectator.headers["Authorization"] = (
            f"Bearer {login_resp.json()['access_token']}"
        )

        target_user_account_id = (await second_spectator.get("/api/users/me")).json()[
            "user_account"
        ]["user_account_id"]

        validate_response(
            test_response=await second_spectator.get("/api/users/me"),
            expected_status_code=200,
        )

        validate_response(
            test_response=await admin_client.post(
                f"/api/logout/user-account/{target_user_account_id}"
            ),
            expected_json_schema=SUCCESS_JSON_SCHEMA,
            expected_status_code=200,
        )

        # Both first and second spectator sessions are now invalid
        validate_response(
            test_response=await second_spectator.get("/api/users/me"),
            expected_status_code=401,
        )
        validate_response(
            test_response=await spectator_client.get("/api/users/me"),
            expected_status_code=401,
        )

        # Non-UUID string: 422 (UUID validation fires before lookup for admin)
        validate_response(
            test_response=await admin_client.post(
                "/api/logout/user-account/invalid-user-account-id"
            ),
            expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )

        # Operator and spectator get 403; invalid ID also returns 403
        # Re-login spectator first so it can make RBAC-denied requests
        login_resp2 = await spectator_client.post(
            "/api/login",
            data={"username": "spectator", "password": "spectator"},
        )
        assert login_resp2.status_code == 200
        spectator_client.headers["Authorization"] = (
            f"Bearer {login_resp2.json()['access_token']}"
        )

        for non_admin in [operator_client, spectator_client]:
            validate_response(
                test_response=await non_admin.post(
                    f"/api/logout/user-account/{target_user_account_id}"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            validate_response(
                test_response=await non_admin.post(
                    "/api/logout/user-account/invalid-user-account-id"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
    finally:
        await second_spectator.aclose()
