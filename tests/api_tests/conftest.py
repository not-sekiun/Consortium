# conftest is a special file name that pytest automatically looks for in the tests
# directory. It is used to define fixtures that can be used in all tests.
import json

import pytest
import requests

from tests.api_tests.utils import (
    get_all_listener_template_ids,
    get_all_user_account_ids,
    validate_response,
)

_JSON_WEB_TOKEN_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {"type": "string"},
        "token_type": {"type": "string"},
    },
    "required": ["access_token", "token_type"],
}


@pytest.fixture(scope="package", autouse=True)
def validate_user_accounts_json_file_before_tests():
    # For end-to-end testing we assume a set of default user account credentials so that
    # the pytest framework can log in and perform tests on the REST API.
    default_user_accounts = [
        {
            "username": "admin",
            "password": "admin",
            "role": "ADMIN",
        },
        {
            "username": "operator",
            "password": "operator",
            "role": "OPERATOR",
        },
        {
            "username": "spectator",
            "password": "spectator",
            "role": "SPECTATOR",
        },
    ]

    # Pytest should be run at project root, so we can assume this when constructing the
    # path to the config file.
    with open("data/server/user_accounts.json") as file:
        user_accounts_json_data = json.load(file)

    # The order of the user accounts in the JSON file does not matter
    for user_account in user_accounts_json_data:
        assert user_account in default_user_accounts


@pytest.fixture(scope="package", autouse=True)
def validate_server_config_json_file_before_tests():
    # For end-to-end testing we assume a set of default server configurations so that
    # the pytest framework can perform tests on the REST API.
    default_server_config = {
        "local_host": "0.0.0.0",
        "local_port": 9999,
        "remote_host_whitelist": [],
        "remote_host_blacklist": [],
        "server_banner": "Apache",
    }

    with open("data/server/server_config.json") as file:
        server_config_json_data = json.load(file)

    # The order of the server configurations in the JSON file does not matter
    for key, value in default_server_config.items():
        assert server_config_json_data[key] == value


@pytest.fixture(scope="package")
def admin_session():
    # login as an admin using form data to get a JSON web token, then create a session
    # that automatically adds the JSON web token to all requests
    session = requests.Session()
    response = validate_response(
        test_response=session.post(
            "http://localhost:9999/api/login",
            data={"username": "admin", "password": "admin"},
        ),
        expected_status_code=200,
        expected_json_schema=_JSON_WEB_TOKEN_RESPONSE_JSON_SCHEMA,
    )
    session.headers.update(
        {"Authorization": f"Bearer {response.json()["access_token"]}"},
    )
    return session


@pytest.fixture(scope="package")
def operator_session():
    # login as an operator using form data to get a JSON web token, then create a
    # session that automatically adds the JSON web token to all requests
    session = requests.Session()
    response = validate_response(
        test_response=session.post(
            "http://localhost:9999/api/login",
            data={"username": "operator", "password": "operator"},
        ),
        expected_status_code=200,
        expected_json_schema=_JSON_WEB_TOKEN_RESPONSE_JSON_SCHEMA,
    )
    session.headers.update(
        {"Authorization": f"Bearer {response.json()["access_token"]}"},
    )
    return session


@pytest.fixture(scope="package")
def spectator_session():
    # login as an operator using form data to get a JSON web token, then create a
    # session that automatically adds the JSON web token to all requests
    session = requests.Session()
    response = validate_response(
        test_response=session.post(
            "http://localhost:9999/api/login",
            data={"username": "spectator", "password": "spectator"},
        ),
        expected_status_code=200,
        expected_json_schema=_JSON_WEB_TOKEN_RESPONSE_JSON_SCHEMA,
    )
    session.headers.update(
        {"Authorization": f"Bearer {response.json()["access_token"]}"},
    )
    return session


@pytest.fixture(params=["admin_session", "operator_session", "spectator_session"])
def session(admin_session, operator_session, spectator_session, request):
    str_to_session_map = {
        "admin_session": admin_session,
        "operator_session": operator_session,
        "spectator_session": spectator_session,
    }
    return str_to_session_map[request.param]


# Create one listener with default values for each available listener template before
# the test starts.
@pytest.fixture
def create_listeners_before_test(
    admin_session: requests.Session,
):
    for listener_template_id in get_all_listener_template_ids(admin_session):
        admin_session.post(
            f"http://localhost:9999/api/listener-templates/{listener_template_id}",
            json={
                option_name: option["default_value"]
                for option_name, option in admin_session.get(
                    f"http://localhost:9999/api/listener-templates/{listener_template_id}",
                )
                .json()["options"]
                .items()
            },
        )

    yield None


# Delete all listeners after the test finishes.
@pytest.fixture
def delete_listeners_after_test(
    admin_session: requests.Session,
):
    yield None

    all_listener_ids = [
        listener["listener_id"]
        for listener in admin_session.get(
            "http://localhost:9999/api/listeners/all",
        ).json()
    ]
    for listener_id in all_listener_ids:
        admin_session.delete(f"http://localhost:9999/api/listeners/{listener_id}")


# Delete all agent generators after the test finishes.
@pytest.fixture
def delete_agent_generators_after_test(
    admin_session: requests.Session,
):
    yield None

    all_agent_generator_ids = [
        agent_generator["agent_generator_id"]
        for agent_generator in admin_session.get(
            "http://localhost:9999/api/agent-generators/all",
        ).json()
    ]
    for agent_generator_id in all_agent_generator_ids:
        admin_session.delete(
            f"http://localhost:9999/api/listeners/{agent_generator_id}",
        )


# We do not write directly to the user_accounts.json file because that will not
# automatically update the user accounts information that is stored in memory on the
# still running server.
@pytest.fixture
def restore_default_user_accounts_after_test(admin_session):
    yield None

    for user_account_id in get_all_user_account_ids(admin_session):
        admin_session.delete(
            f"http://localhost:9999/api/user-accounts/{user_account_id}",
        )
    admin_session.post(
        "http://localhost:9999/api/user-accounts",
        json={
            "username": "admin",
            "password": "admin",
            "role": "ADMIN",
        },
    )
    admin_session.post(
        "http://localhost:9999/api/user-accounts",
        json={
            "username": "operator",
            "password": "operator",
            "role": "OPERATOR",
        },
    )
    admin_session.post(
        "http://localhost:9999/api/user-accounts",
        json={
            "username": "spectator",
            "password": "spectator",
            "role": "SPECTATOR",
        },
    )


@pytest.fixture(scope="package", autouse=True)
def logout_all_sessions(admin_session, operator_session, spectator_session):
    # yielding None allows the fixture to run after all tests have completed
    yield None
    admin_session.post("http://localhost:9999/api/logout")
    operator_session.post("http://localhost:9999/api/logout")
    spectator_session.post("http://localhost:9999/api/logout")
