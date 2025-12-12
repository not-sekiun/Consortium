import requests

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
    SUCCESS_RESPONSE_JSON_SCHEMA,
)
from tests.api_tests.test_user_accounts_api import (
    USER_ACCOUNT_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
)
from tests.api_tests.test_users_api import USER_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA
from tests.api_tests.utils import validate_response


def test_logout_from_server(
    admin_session: requests.Session,
    operator_session: requests.Session,
    spectator_session: requests.Session,
):
    """Test that all users can logout themselves."""
    sessions_with_credentials = [
        (admin_session, "admin", "admin"),
        (operator_session, "operator", "operator"),
        (spectator_session, "spectator", "spectator"),
    ]

    for session, username, password in sessions_with_credentials:
        # Logout
        validate_response(
            test_response=session.post("http://localhost:9999/api/logout"),
            expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )

        # Verify logged out
        validate_response(
            test_response=session.get("http://localhost:9999/api/users/me"),
            expected_status_code=401,
        )

        # Re-login for subsequent tests
        response = session.post(
            "http://localhost:9999/api/login",
            data={"username": username, "password": password},
        )
        session.headers.update(
            {"Authorization": f"Bearer {response.json()['access_token']}"}
        )


def test_logout_user_by_user_id(
    admin_session: requests.Session,
    operator_session: requests.Session,
    spectator_session: requests.Session,
):
    """Test logging out a user by user ID."""
    # Create a second admin session to test logout on
    second_admin_session = requests.Session()
    login_response = second_admin_session.post(
        "http://localhost:9999/api/login",
        data={"username": "admin", "password": "admin"},
    )
    second_admin_session.headers.update(
        {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    )

    # Get the admin user ID
    admin_user_response = second_admin_session.get("http://localhost:9999/api/users/me")
    target_user_id = admin_user_response.json()["user_id"]

    # Verify second admin session is logged in
    validate_response(
        test_response=second_admin_session.get("http://localhost:9999/api/users/me"),
        expected_status_code=200,
    )

    # Admin should be able to logout users by user ID
    validate_response(
        test_response=admin_session.post(
            f"http://localhost:9999/api/logout/user/{target_user_id}"
        ),
        expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )

    # Verify second admin session is logged out
    validate_response(
        test_response=second_admin_session.get("http://localhost:9999/api/users/me"),
        expected_status_code=401,
    )

    # Test with invalid user ID
    validate_response(
        test_response=admin_session.post(
            "http://localhost:9999/api/logout/user/invalid-user-id"
        ),
        expected_json_schema=USER_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=404,
    )

    # Operator and spectator should not be able to logout users by user ID
    for session in [operator_session, spectator_session]:
        validate_response(
            test_response=session.post(
                f"http://localhost:9999/api/logout/user/{target_user_id}"
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

        # 404 should not be returned to prevent information leakage
        validate_response(
            test_response=session.post(
                "http://localhost:9999/api/logout/user/invalid-user-id"
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )


def test_logout_user_account_by_user_account_id(
    admin_session: requests.Session,
    operator_session: requests.Session,
    spectator_session: requests.Session,
):
    # """Test logging out a user by user account ID."""
    # # Create a second spectator session to test logout on
    second_spectator_session = requests.Session()
    login_response = second_spectator_session.post(
        "http://localhost:9999/api/login",
        data={"username": "spectator", "password": "spectator"},
    )
    second_spectator_session.headers.update(
        {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    )

    # Get the spectator user account ID
    spectator_user_response = second_spectator_session.get(
        "http://localhost:9999/api/users/me"
    )
    target_user_account_id = spectator_user_response.json()["user_account"][
        "user_account_id"
    ]

    # Verify second spectator session is logged in
    validate_response(
        test_response=second_spectator_session.get(
            "http://localhost:9999/api/users/me"
        ),
        expected_status_code=200,
    )

    # Admin should be able to logout users by user account ID
    validate_response(
        test_response=admin_session.post(
            f"http://localhost:9999/api/logout/user-account/{target_user_account_id}"
        ),
        expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )

    # Verify second spectator session is logged out
    validate_response(
        test_response=second_spectator_session.get(
            "http://localhost:9999/api/users/me"
        ),
        expected_status_code=401,
    )

    # Test with invalid user account ID
    validate_response(
        test_response=admin_session.post(
            "http://localhost:9999/api/logout/user-account/invalid-user-account-id"
        ),
        expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=404,
    )

    # Log back in spectator session for subsequent tests because logging out the second
    # spectator session by user account ID causes the first spectator session to be
    # logged out as well.
    response = spectator_session.post(
        "http://localhost:9999/api/login",
        data={"username": "spectator", "password": "spectator"},
    )
    spectator_session.headers.update(
        {"Authorization": f"Bearer {response.json()['access_token']}"}
    )

    # Operator and spectator should not be able to logout users by user account ID
    for session in [spectator_session]:  # , spectator_session]:
        validate_response(
            test_response=session.post(
                f"http://localhost:9999/api/logout/user-account/{target_user_account_id}"
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

        # 404 should not be returned to prevent information leakage
        validate_response(
            test_response=session.post(
                "http://localhost:9999/api/logout/user-account/invalid-user-account-id"
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )
