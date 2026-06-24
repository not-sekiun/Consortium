import httpx
import pytest

from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

JWT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {"type": "string"},
        "token_type": {"type": "string"},
    },
    "required": ["access_token", "token_type"],
}
ALREADY_LOGGED_IN_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["ALREADY_LOGGED_IN_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


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
            expected_json_schema=JWT_JSON_SCHEMA,
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


async def test_login_while_already_logged_in_returns_409(admin_client):
    """A second login attempt while already logged in returns 409."""
    validate_response(
        test_response=await admin_client.post(
            "/api/login",
            data={"username": "admin", "password": "admin"},
        ),
        expected_json_schema=ALREADY_LOGGED_IN_ERROR_JSON_SCHEMA,
        expected_status_code=409,
    )


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
                expected_json_schema=JWT_JSON_SCHEMA,
                expected_status_code=200,
            )
            await client.post("/api/logout")
