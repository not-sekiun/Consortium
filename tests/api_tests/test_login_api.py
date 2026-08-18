import httpx
import pytest

from tests.api_tests.framework_components_json_response_schemas import (
    JSON_WEB_TOKEN_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


async def test_login_with_valid_credentials(app):
    """Successful login returns a JWT with access_token and token_type."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        validate_response(
            test_response=await client.post(
                "/api/login",
                data={"username": "admin", "password": "admin"},
            ),
            expected_json_schema=JSON_WEB_TOKEN_JSON_SCHEMA,
            expected_status_code=200,
        )
        await client.post("/api/logout")


async def test_login_with_wrong_password_returns_401(app):
    """Login with an incorrect password returns an empty 401."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/login",
            data={"username": "admin", "password": "wrong-password"},
        )
        assert response.status_code == 401
        assert not response.content, "Expected empty body on failed login"


async def test_login_with_unknown_username_returns_401(app):
    """Login with an unknown username returns an empty 401."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/login",
            data={"username": "does-not-exist", "password": "somepassword"},
        )
        assert response.status_code == 401
        assert not response.content, "Expected empty body on failed login"


async def test_login_while_already_logged_in_returns_new_jwt(admin_client):
    """A second login attempt while already logged in issues a fresh JWT (idempotent login)."""
    old_token = admin_client.headers["Authorization"]
    response = await admin_client.post(
        "/api/login",
        data={"username": "admin", "password": "admin"},
    )
    validate_response(
        test_response=response,
        expected_json_schema=JSON_WEB_TOKEN_JSON_SCHEMA,
        expected_status_code=200,
    )
    new_token = f"Bearer {response.json()['access_token']}"
    assert new_token != old_token, "Expected a new JWT to be issued on re-login"
    # Restore original token so session-scoped client is unaffected by this test.
    admin_client.headers["Authorization"] = old_token


async def test_all_user_roles_can_login(app):
    """Admin, operator, and spectator can all log in successfully."""
    credentials = [
        ("admin", "admin"),
        ("operator", "operator"),
        ("spectator", "spectator"),
    ]
    for username, password in credentials:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            validate_response(
                test_response=await client.post(
                    "/api/login",
                    data={"username": username, "password": password},
                ),
                expected_json_schema=JSON_WEB_TOKEN_JSON_SCHEMA,
                expected_status_code=200,
            )
            await client.post("/api/logout")
