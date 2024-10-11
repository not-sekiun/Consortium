import requests

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

USER_RESPONSE_JSON_SCHEMA = {
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
ALL_USERS_RESPONSE_JSON_SCHEMA = {
    "type": "array",
    "items": USER_RESPONSE_JSON_SCHEMA,
}
USER_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA = {
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


def test_get_own_user(session: requests.Session):
    validate_response(
        test_response=session.get("http://localhost:9999/api/users/me"),
        expected_json_schema=USER_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )


def test_get_all_users(admin_session: requests.Session, session: requests.Session):
    if session == admin_session:
        # Test for admin sessions.
        validate_response(
            test_response=session.get("http://localhost:9999/api/users/all"),
            expected_json_schema=ALL_USERS_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )
    else:
        # Test for operator and spectator sessions.
        validate_response(
            test_response=session.get("http://localhost:9999/api/users/all"),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )


def test_get_user_by_user_id(
    admin_session: requests.Session,
    session: requests.Session,
):
    all_users_user_ids = [
        user["user_id"]
        for user in admin_session.get("http://localhost:9999/api/users/all").json()
    ]

    if session == admin_session:
        for user_id in all_users_user_ids:
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/users/{user_id}",
                ),
                expected_json_schema=USER_RESPONSE_JSON_SCHEMA,
                expected_status_code=200,
            )
        validate_response(
            test_response=admin_session.get(
                "http://localhost:9999/api/users/invalid-user-id",
            ),
            expected_json_schema=USER_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        for user_id in all_users_user_ids:
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/users/{user_id}",
                ),
                expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
                expected_status_code=403,
            )
        # 404 should not be returned despite the user ID being an invalid user ID to
        # prevent information leakage to low privileged users (OPERATOR and SPECTATOR).
        validate_response(
            test_response=session.get(
                "http://localhost:9999/api/users/invalid-user-id",
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )
