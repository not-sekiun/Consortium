import uuid

from tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
    SUCCESS_RESPONSE_JSON_SCHEMA,
)
from tests.utils import validate_response

USER_ACCOUNT_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "user_account_id": {"type": "string"},
        "username": {"type": "string"},
        "password": {"type": "string"},
        "role": {"type": "string", "enum": ["ADMIN", "OPERATOR", "SPECTATOR"]},
    },
    "required": [
        "user_account_id",
        "username",
        "password",
        "role",
    ],
}
ALL_USER_ACCOUNTS_RESPONSE_JSON_SCHEMA = {
    "type": "array",
    "items": USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
}
USER_ACCOUNT_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA = {
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
DUPLICATE_USER_ACCOUNT_CREATION_ERROR_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["DUPLICATE_USER_ACCOUNT_CREATION_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


def test_create_and_delete_user_account(
    admin_session,
    operator_session,
    spectator_session,
):
    username = uuid.uuid4().hex
    password = uuid.uuid4().hex

    # admin_session test
    user_account_id = validate_response(
        test_response=admin_session.post(
            "http://localhost:9999/api/user_accounts",
            json={"username": username, "password": password, "role": "ADMIN"},
        ),
        expected_json_schema=USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
        expected_status_code=201,
    ).json()["user_account_id"]
    validate_response(
        test_response=admin_session.get(
            f"http://localhost:9999/api/user_accounts/{user_account_id}",
        ),
        expected_json_schema=USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
        # Don't call it response because it will shadow the response variable from the
        # outer scope
        validator_function=lambda response: all(
            (
                response.json()["username"] == username,
                response.json()["password"] == password,
                response.json()["role"] == "ADMIN",
            ),
        ),
    )

    # Test the deletion of the randomly created temporary user account
    validate_response(
        test_response=admin_session.delete(
            f"http://localhost:9999/api/user_accounts/{user_account_id}",
        ),
        expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )
    validate_response(
        test_response=admin_session.get(
            f"http://localhost:9999/api/user_accounts/{user_account_id}",
        ),
        expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=404,
    )

    # Test the creation of a user account with a duplicate username
    validate_response(
        test_response=admin_session.post(
            "http://localhost:9999/api/user_accounts",
            json={"username": "admin", "password": "admin", "role": "ADMIN"},
        ),
        expected_json_schema=DUPLICATE_USER_ACCOUNT_CREATION_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=409,
    )

    # operator_session and spectator_session test
    def run_session_test(session):
        validate_response(
            test_response=session.post(
                "http://localhost:9999/api/user_accounts",
                json={"username": username, "password": password, "role": "ADMIN"},
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

    run_session_test(operator_session)
    run_session_test(spectator_session)


def test_get_own_user_account_info(admin_session, operator_session, spectator_session):
    def run_session_test(session):
        validate_response(
            test_response=session.get("http://localhost:9999/api/user_accounts/me"),
            expected_json_schema=USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )

    run_session_test(admin_session)
    run_session_test(operator_session)
    run_session_test(spectator_session)


def test_get_all_user_accounts_info(admin_session, operator_session, spectator_session):
    def run_session_test(session):
        validate_response(
            test_response=session.get("http://localhost:9999/api/user_accounts/all"),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

    validate_response(
        test_response=admin_session.get("http://localhost:9999/api/user_accounts/all"),
        expected_json_schema=ALL_USER_ACCOUNTS_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )
    run_session_test(operator_session)
    run_session_test(spectator_session)


def test_get_user_account_info_by_user_account_id(
    admin_session,
    operator_session,
    spectator_session,
):
    all_user_account_user_account_ids = [
        user_account["user_account_id"]
        for user_account in admin_session.get(
            "http://localhost:9999/api/user_accounts/all",
        ).json()
    ]

    def run_session_test(session):
        validate_response(
            test_response=session.get(
                f"http://localhost:9999/api/user_accounts/{user_account_id}",
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

    for user_account_id in all_user_account_user_account_ids:
        validate_response(
            test_response=admin_session.get(
                f"http://localhost:9999/api/user_accounts/{user_account_id}",
            ),
            expected_json_schema=USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )
        run_session_test(operator_session)
        run_session_test(spectator_session)


def test_update_own_user_account_password(
    admin_session,
    operator_session,
    spectator_session,
):
    password = uuid.uuid4().hex

    # admin_session and operator_session test
    def run_session_test(session):
        validate_response(
            session.patch(
                f"http://localhost:9999/api/user_accounts/me/password",
                json={"password": password},
            ),
            expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )
        validate_response(
            test_response=session.get(f"http://localhost:9999/api/user_accounts/me"),
            expected_json_schema=USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda response: response.json()["password"] == password,
        )

    run_session_test(admin_session)
    run_session_test(operator_session)

    # spectator_session test
    validate_response(
        spectator_session.patch(
            f"http://localhost:9999/api/user_accounts/me/password",
            json={"password": password},
        ),
        expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=403,
    )

    # restore the original default passwords for the modified accounts
    admin_session.patch(
        f"http://localhost:9999/api/user_accounts/me/password",
        json={"password": "admin"},
    )
    operator_session.patch(
        f"http://localhost:9999/api/user_accounts/me/password",
        json={"password": "operator"},
    )


def test_update_user_account_password_by_user_account_id(
    admin_session,
    operator_session,
    spectator_session,
):
    username = uuid.uuid4().hex
    old_password = uuid.uuid4().hex
    new_password = uuid.uuid4().hex

    # admin_session test
    user_account_id = admin_session.post(
        "http://localhost:9999/api/user_accounts",
        json={"username": username, "password": old_password, "role": "ADMIN"},
    ).json()["user_account_id"]
    validate_response(
        test_response=admin_session.patch(
            f"http://localhost:9999/api/user_accounts/{user_account_id}/password",
            json={"password": new_password},
        ),
        expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )
    validate_response(
        test_response=admin_session.get(
            f"http://localhost:9999/api/user_accounts/{user_account_id}",
        ),
        expected_json_schema=USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: response.json()["password"] == new_password,
    )

    # operator_session and spectator_session test
    admin_session.post(
        f"http://localhost:9999/api/user_accounts/{user_account_id}/password",
        json={"password": old_password},
    )

    def run_session_test(session):
        validate_response(
            test_response=session.patch(
                f"http://localhost:9999/api/user_accounts/{user_account_id}/password",
                json={"password": new_password},
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

    run_session_test(operator_session)
    run_session_test(spectator_session)

    admin_session.delete(f"http://localhost:9999/api/user_accounts/{user_account_id}")


def test_update_user_account_role_by_user_account_id(
    admin_session,
    operator_session,
    spectator_session,
):
    username = uuid.uuid4().hex
    password = uuid.uuid4().hex
    old_role = "ADMIN"
    new_role = "OPERATOR"

    # admin_session test
    user_account_id = admin_session.post(
        "http://localhost:9999/api/user_accounts",
        json={"username": username, "password": password, "role": old_role},
    ).json()["user_account_id"]
    validate_response(
        test_response=admin_session.patch(
            f"http://localhost:9999/api/user_accounts/{user_account_id}/role",
            json={"role": new_role},
        ),
        expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )
    validate_response(
        test_response=admin_session.get(
            f"http://localhost:9999/api/user_accounts/{user_account_id}",
        ),
        expected_json_schema=USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: response.json()["role"] == new_role,
    )

    # operator_session and spectator_session test
    admin_session.post(
        f"http://localhost:9999/api/user_accounts/{user_account_id}/role",
        json={"role": old_role},
    )

    def run_session_test(session):
        validate_response(
            test_response=session.patch(
                f"http://localhost:9999/api/user_accounts/{user_account_id}/role",
                json={"role": new_role},
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

    run_session_test(operator_session)
    run_session_test(spectator_session)

    admin_session.delete(f"http://localhost:9999/api/user_accounts/{user_account_id}")


def test_delete_user_account_by_user_account_id(
    admin_session,
    operator_session,
    spectator_session,
):
    username = uuid.uuid4().hex
    password = uuid.uuid4().hex

    # admin_session test
    user_account_id = admin_session.post(
        "http://localhost:9999/api/user_accounts",
        json={"username": username, "password": password, "role": "ADMIN"},
    ).json()["user_account_id"]
    validate_response(
        test_response=admin_session.get(
            f"http://localhost:9999/api/user_accounts/{user_account_id}",
        ),
        expected_json_schema=USER_ACCOUNT_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )
    validate_response(
        test_response=admin_session.delete(
            f"http://localhost:9999/api/user_accounts/{user_account_id}",
        ),
        expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )
    validate_response(
        test_response=admin_session.get(
            f"http://localhost:9999/api/user_accounts/{user_account_id}",
        ),
        expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=404,
    )

    # operator_session and spectator_session test
    user_account_id = admin_session.post(
        "http://localhost:9999/api/user_accounts",
        json={"username": username, "password": password, "role": "ADMIN"},
    ).json()["user_account_id"]

    def run_session_test(session):
        validate_response(
            test_response=session.delete(
                f"http://localhost:9999/api/user_accounts/{user_account_id}",
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

    run_session_test(operator_session)
    run_session_test(spectator_session)

    admin_session.delete(f"http://localhost:9999/api/user_accounts/{user_account_id}")


def test_delete_own_user_account(admin_session, operator_session, spectator_session):
    def run_session_test(session):
        user = session.get("http://localhost:9999/api/user_accounts/me").json()
        validate_response(
            test_response=session.delete(f"http://localhost:9999/api/user_accounts/me"),
            expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )
        validate_response(
            test_response=session.get(f"http://localhost:9999/api/user_accounts/me"),
            expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=404,
        )
        # restore the deleted account
        (
            admin_session.post(
                "http://localhost:9999/api/user_accounts",
                json={
                    "username": user["username"],
                    "password": user["password"],
                    "role": user["role"],
                },
            ),
        )

    run_session_test(admin_session)
    run_session_test(operator_session)

    # spectator_session test
    validate_response(
        test_response=spectator_session.delete(
            f"http://localhost:9999/api/user_accounts/me",
        ),
        expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=403,
    )
