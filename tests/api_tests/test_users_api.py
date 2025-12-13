import requests

from tests.api_tests.common_json_response_schemas import FORBIDDEN_ERROR_JSON_SCHEMA
from tests.api_tests.utils import validate_response

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


def test_get_own_user(session: requests.Session):
    validate_response(
        test_response=session.get("http://localhost:9999/api/users/me"),
        expected_json_schema=USER_JSON_SCHEMA,
        expected_status_code=200,
    )


def test_get_all_users(
    admin_session: requests.Session,
    operator_session: requests.Session,
    session: requests.Session,
):
    if session in (admin_session, operator_session):
        # Test for admin and operator sessions.
        validate_response(
            test_response=session.get("http://localhost:9999/api/users/all"),
            expected_json_schema=ALL_USERS_JSON_SCHEMA,
            expected_status_code=200,
        )
    else:
        # Test for spectator sessions.
        validate_response(
            test_response=session.get("http://localhost:9999/api/users/all"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


def test_get_user_by_user_id(
    admin_session: requests.Session,
    operator_session: requests.Session,
    session: requests.Session,
):
    all_users_user_ids = [
        user["user_id"]
        for user in admin_session.get("http://localhost:9999/api/users/all").json()
    ]

    if session in (admin_session, operator_session):
        for user_id in all_users_user_ids:
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/users/{user_id}",
                ),
                expected_json_schema=USER_JSON_SCHEMA,
                expected_status_code=200,
            )
        validate_response(
            test_response=admin_session.get(
                "http://localhost:9999/api/users/invalid-user-id",
            ),
            expected_json_schema=USER_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        for user_id in all_users_user_ids:
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/users/{user_id}",
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
        # 404 should not be returned despite the user ID being an invalid user ID to
        # prevent information leakage to low privileged users (OPERATOR and SPECTATOR).
        validate_response(
            test_response=session.get(
                "http://localhost:9999/api/users/invalid-user-id",
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


def test_update_own_display_name(session: requests.Session):
    # Get the current user's information
    current_user_response = validate_response(
        test_response=session.get("http://localhost:9999/api/users/me"),
        expected_json_schema=USER_JSON_SCHEMA,
        expected_status_code=200,
    )
    original_display_name = current_user_response.json()["display_name"]

    # Update the display name
    updated_user_response = validate_response(
        test_response=session.patch(
            "http://localhost:9999/api/users/me",
            json={"display_name": "Updated Display Name"},
        ),
        expected_json_schema=USER_JSON_SCHEMA,
        expected_status_code=200,
    )
    assert updated_user_response.json()["display_name"] == "Updated Display Name"

    # Restore the original display name
    validate_response(
        test_response=session.patch(
            "http://localhost:9999/api/users/me",
            json={"display_name": original_display_name},
        ),
        expected_json_schema=USER_JSON_SCHEMA,
        expected_status_code=200,
    )


def test_update_user_display_name_by_user_id(
    admin_session: requests.Session,
    operator_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    # Get all users
    all_users = admin_session.get("http://localhost:9999/api/users/all").json()

    # Find a user that is not the current session user
    current_user = session.get("http://localhost:9999/api/users/me").json()
    target_user = next(
        user for user in all_users if user["user_id"] != current_user["user_id"]
    )
    target_user_id = target_user["user_id"]
    original_display_name = target_user["display_name"]

    if session == admin_session:
        # Admin should be able to update any user's display name
        updated_user_response = validate_response(
            test_response=session.patch(
                f"http://localhost:9999/api/users/{target_user_id}",
                json={"display_name": "Admin Updated Name"},
            ),
            expected_json_schema=USER_JSON_SCHEMA,
            expected_status_code=200,
        )
        assert updated_user_response.json()["display_name"] == "Admin Updated Name"

        # Restore the original display name
        validate_response(
            test_response=session.patch(
                f"http://localhost:9999/api/users/{target_user_id}",
                json={"display_name": original_display_name},
            ),
            expected_json_schema=USER_JSON_SCHEMA,
            expected_status_code=200,
        )

        # Test with invalid user ID
        validate_response(
            test_response=session.patch(
                "http://localhost:9999/api/users/invalid-user-id",
                json={"display_name": "Should Fail"},
            ),
            expected_json_schema=USER_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        # Operator and spectator should not be able to update other users' display names
        validate_response(
            test_response=session.patch(
                f"http://localhost:9999/api/users/{target_user_id}",
                json={"display_name": "Should Fail"},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )

        # 404 should not be returned despite invalid user ID to prevent information leakage
        validate_response(
            test_response=session.patch(
                "http://localhost:9999/api/users/invalid-user-id",
                json={"display_name": "Should Fail"},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )
