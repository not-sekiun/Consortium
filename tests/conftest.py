# conftest is a special file name that pytest automatically looks for in the
# tests directory. It is used to define fixtures that can be used in all tests.
import json

import jsonschema
import pytest
import requests

_JSON_WEB_TOKEN_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {"type": "string"},
        "token_type": {"type": "string"},
    },
    "required": ["access_token", "token_type"],
}


@pytest.fixture(scope="session", autouse=True)
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


@pytest.fixture(scope="session", autouse=True)
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

    with open("data/server/config.json") as file:
        server_config_json_data = json.load(file)

    # The order of the server configurations in the JSON file does not matter
    for key, value in default_server_config.items():
        assert server_config_json_data[key] == value


# scope="session" means that the fixture is created once per test session and is shared
# across all tests modules and test functions. This dramatically increases testing speed
# because requests is very slow without the use of shared sessions.
@pytest.fixture(scope="session")
def admin_session():
    # login as an admin using form data to get a JSON web token, then create a session
    # that automatically adds the JSON web token to all requests
    session = requests.Session()
    response = session.post(
        "http://localhost:9999/api/login",
        data={"username": "admin", "password": "admin"},
    )

    assert response.status_code == 200

    try:
        jsonschema.validate(response.json(), _JSON_WEB_TOKEN_RESPONSE_JSON_SCHEMA)
    except jsonschema.exceptions.ValidationError as exc:
        pytest.fail(exc.message)

    session.headers.update(
        {"Authorization": f"Bearer {response.json()["access_token"]}"},
    )
    return session


@pytest.fixture(scope="session")
def operator_session():
    # login as an operator using form data to get a JSON web token, then create a
    # session that automatically adds the JSON web token to all requests
    session = requests.Session()
    response = session.post(
        "http://localhost:9999/api/login",
        data={"username": "operator", "password": "operator"},
    )

    assert response.status_code == 200

    try:
        jsonschema.validate(response.json(), _JSON_WEB_TOKEN_RESPONSE_JSON_SCHEMA)
    except jsonschema.exceptions.ValidationError as exc:
        pytest.fail(exc.message)

    session.headers.update(
        {"Authorization": f"Bearer {response.json()["access_token"]}"},
    )
    return session


@pytest.fixture(scope="session")
def spectator_session():
    # login as an operator using form data to get a JSON web token, then create a
    # session that automatically adds the JSON web token to all requests
    session = requests.Session()
    response = session.post(
        "http://localhost:9999/api/login",
        data={"username": "spectator", "password": "spectator"},
    )

    assert response.status_code == 200

    try:
        jsonschema.validate(response.json(), _JSON_WEB_TOKEN_RESPONSE_JSON_SCHEMA)
    except jsonschema.exceptions.ValidationError as exc:
        pytest.fail(exc.message)

    session.headers.update(
        {"Authorization": f"Bearer {response.json()["access_token"]}"},
    )
    return session


@pytest.fixture(scope="session", autouse=True)
def logout_all_sessions(admin_session, operator_session, spectator_session):
    # yielding None allows the fixture to run after all tests have completed
    yield None
    admin_session.post("http://localhost:9999/api/logout")
    operator_session.post("http://localhost:9999/api/logout")
    spectator_session.post("http://localhost:9999/api/logout")
