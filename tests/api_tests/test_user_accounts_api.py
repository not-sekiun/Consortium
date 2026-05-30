import uuid

import pytest
import requests

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    SUCCESS_JSON_SCHEMA,
)
from tests.api_tests.utils import get_all_user_account_ids, validate_response

USER_ACCOUNT_JSON_SCHEMA = {
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
DUPLICATE_USER_ACCOUNT_CREATION_ERROR_JSON_SCHEMA = {
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


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
@pytest.mark.parametrize(
    # test_user_account is a tuple of (username, password, role)
    "test_user_account",
    [
        (uuid.uuid4().hex, uuid.uuid4().hex, "ADMIN"),
        (uuid.uuid4().hex, uuid.uuid4().hex, "OPERATOR"),
        (uuid.uuid4().hex, uuid.uuid4().hex, "SPECTATOR"),
    ],
)
def test_create_user_account(
    admin_session: requests.Session,
    session: requests.Session,
    test_user_account: tuple[str, str, str],
):
    if session == admin_session:
        # Test for admin sessions.
        user_account = validate_response(
            test_response=admin_session.post(
                "http://localhost:9999/api/user-accounts",
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
            test_response=admin_session.get(
                f"http://localhost:9999/api/user-accounts/{user_account['user_account_id']}",
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            # Don't call the lambda variable response because it will shadow the
            # response variable from the outer scope
            validator_function=lambda response: all(
                (
                    response.json()["username"] == test_user_account[0],
                    response.json()["password"] == test_user_account[1],
                    response.json()["role"] == test_user_account[2],
                ),
            ),
        )
    else:
        # Test for operator and spectator sessions.
        validate_response(
            test_response=session.post(
                "http://localhost:9999/api/user-accounts",
                json={
                    "username": test_user_account[0],
                    "password": test_user_account[1],
                    "role": test_user_account[2],
                },
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


def test_get_user_account_by_user_account_id(
    admin_session: requests.Session,
    session: requests.Session,
):
    if session == admin_session:
        for user_account_id in get_all_user_account_ids(admin_session):
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/user-accounts/{user_account_id}",
                ),
                expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
                expected_status_code=200,
            )
    else:
        for user_account_id in get_all_user_account_ids(admin_session):
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/user-accounts/{user_account_id}",
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


def test_get_all_user_accounts(
    admin_session: requests.Session,
    session: requests.Session,
):
    if session == admin_session:
        # Test for admin sessions.
        validate_response(
            test_response=session.get("http://localhost:9999/api/user-accounts/all"),
            expected_json_schema=ALL_USER_ACCOUNTS_JSON_SCHEMA,
            expected_status_code=200,
        )
    else:
        # Test for operator and spectator sessions.
        validate_response(
            test_response=session.get("http://localhost:9999/api/user-accounts/all"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


# TODO: The restored user account information does not get reflected in the server. Fix
#  this
@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
def test_update_user_account_username_by_user_account_id(
    admin_session: requests.Session,
    operator_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    new_username = uuid.uuid4().hex
    user = session.get("http://localhost:9999/api/users/me").json()
    user_account_id = user["user_account"]["user_account_id"]

    if session == admin_session:
        validate_response(
            session.patch(
                f"http://localhost:9999/api/user-accounts/{user_account_id}",
                json={
                    "username": new_username,
                },
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda response: (
                response.json()["username"] == new_username
            ),
        )
    else:
        validate_response(
            session.patch(
                f"http://localhost:9999/api/user-accounts/{user_account_id}",
                json={
                    "username": new_username,
                },
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


# TODO: The restored user account information does not get reflected in the server. Fix
#  this
@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
def test_update_user_account_password_by_user_account_id(
    admin_session: requests.Session,
    operator_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    user_account = session.get("http://localhost:9999/api/user-accounts/me").json()
    user_account_id = user_account["user_account_id"]
    new_password = uuid.uuid4().hex

    if session == admin_session:
        validate_response(
            session.patch(
                f"http://localhost:9999/api/user-accounts/{user_account_id}",
                json={
                    "password": new_password,
                },
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda response: (
                response.json()["password"] == new_password
            ),
        )
    else:
        validate_response(
            session.patch(
                f"http://localhost:9999/api/user-accounts/{user_account_id}",
                json={"password": new_password},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


# TODO: The restored user account information does not get reflected in the server. Fix
#  this
@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
def test_update_user_account_role_by_user_account_id(
    admin_session: requests.Session,
    operator_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    old_role_str_to_new_role_str_map = {
        "ADMIN": "ADMIN",
        "OPERATOR": "SPECTATOR",
        "SPECTATOR": "ADMIN",
    }
    user_account = session.get("http://localhost:9999/api/user-accounts/me").json()
    user_account_id = user_account["user_account_id"]
    new_role = old_role_str_to_new_role_str_map[user_account["role"]]

    if session == admin_session:
        validate_response(
            session.patch(
                f"http://localhost:9999/api/user-accounts/{user_account_id}",
                json={
                    "role": new_role,
                },
            ),
            expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
            expected_status_code=200,
            validator_function=lambda response: response.json()["role"] == new_role,
        )
    else:
        validate_response(
            session.patch(
                f"http://localhost:9999/api/user-accounts/{user_account_id}",
                json={
                    "role": new_role,
                },
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
def test_update_user_account_by_user_account_id(
    admin_session: requests.Session,
    session: requests.Session,
):
    if session == admin_session:
        old_role_str_to_new_role_str_map = {
            "ADMIN": "ADMIN",
            "OPERATOR": "SPECTATOR",
            "SPECTATOR": "ADMIN",
        }
        for user_account_id in get_all_user_account_ids(admin_session):
            user_account = session.get(
                "http://localhost:9999/api/user-accounts/me",
            ).json()
            new_username = uuid.uuid4().hex
            new_password = uuid.uuid4().hex
            new_role = old_role_str_to_new_role_str_map[user_account["role"]]
            validate_response(
                test_response=admin_session.patch(
                    f"http://localhost:9999/api/user-accounts/{user_account_id}",
                    json={
                        "username": new_username,
                        "password": new_password,
                        "role": new_role,
                    },
                ),
                expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
                expected_status_code=200,
                # Bind the variables to avoid late binding issue in lambda
                validator_function=lambda response,
                new_username_bind=new_username,
                new_password_bind=new_password,
                new_role_bind=new_role: (
                    response.json()["username"] == new_username_bind
                    and response.json()["password"] == new_password_bind
                    and response.json()["role"] == new_role_bind
                ),
            )
    else:
        for user_account_id in get_all_user_account_ids(admin_session):
            user_account = session.get(
                "http://localhost:9999/api/user-accounts/me",
            ).json()
            new_username = uuid.uuid4().hex
            old_password = user_account["password"]
            new_password = uuid.uuid4().hex
            new_role = "OPERATOR"
            validate_response(
                test_response=session.patch(
                    f"http://localhost:9999/api/user-accounts/{user_account_id}",
                    json={
                        "username": new_username,
                        "password": {
                            "new_password": new_password,
                            "old_password": old_password,
                        },
                        "role": new_role,
                    },
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


# @pytest.mark.usefixtures("restore_default_user_accounts_after_test")
# def test_update_own_user_account(
#     admin_session: requests.Session,
#     operator_session: requests.Session,
#     spectator_session: requests.Session,
#     session: requests.Session,
# ):
#     new_username = uuid.uuid4().hex
#     new_password = uuid.uuid4().hex
#
#     if session == admin_session:
#         new_role = "OPERATOR"
#         validate_response(
#             session.patch(
#                 "http://localhost:9999/api/user-accounts/me",
#                 json={
#                     "username": new_username,
#                     "password": new_password,
#                     "role": new_role,
#                 },
#             ),
#             expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
#             expected_status_code=200,
#             validator_function=lambda response: response.json()["username"]
#             == new_username
#             and response.json()["password"] == new_password
#             and response.json()["role"] == new_role,
#         )
#     elif session == operator_session:
#         new_role = "ADMIN"
#         validate_response(
#             session.patch(
#                 "http://localhost:9999/api/user-accounts/me",
#                 json={
#                     "username": new_username,
#                     "password": new_password,
#                     "role": new_role,
#                 },
#             ),
#             expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
#             expected_status_code=403,
#         )
#         validate_response(
#             session.patch(
#                 "http://localhost:9999/api/user-accounts/me",
#                 json={
#                     "username": new_username,
#                     "password": new_password,
#                 },
#             ),
#             expected_json_schema=USER_ACCOUNT_JSON_SCHEMA,
#             expected_status_code=200,
#             validator_function=lambda response: response.json()["username"]
#             == new_username
#             and response.json()["password"] == new_password
#             and response.json()["role"] == "OPERATOR",
#         )
#     else:
#         # Test for spectator sessions.
#         new_role = "ADMIN"
#         validate_response(
#             spectator_session.patch(
#                 "http://localhost:9999/api/user-accounts/me",
#                 json={
#                     "username": new_username,
#                     "password": new_password,
#                     "role": new_role,
#                 },
#             ),
#             expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
#             expected_status_code=403,
#         )
#
#


@pytest.mark.usefixtures("restore_default_user_accounts_after_test")
def test_delete_user_account_by_user_account_id(
    admin_session: requests.Session,
    session: requests.Session,
):
    if session == admin_session:
        # Test for admin sessions.
        # Deleting a user account will not log a user out from the associated account.
        for user_account_id in get_all_user_account_ids(admin_session):
            validate_response(
                test_response=session.delete(
                    f"http://localhost:9999/api/user-accounts/{user_account_id}",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/user-accounts/{user_account_id}",
                ),
                expected_json_schema=USER_ACCOUNT_NOT_FOUND_ERROR_JSON_SCHEMA,
                expected_status_code=404,
            )
    else:
        # Test for operator and spectator sessions.
        for user_account_id in get_all_user_account_ids(admin_session):
            validate_response(
                test_response=session.delete(
                    f"http://localhost:9999/api/user-accounts/{user_account_id}",
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
