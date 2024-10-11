from typing import Callable

import jsonschema
import pytest
import requests


def validate_response(
    test_response: requests.Response,
    expected_json_schema: dict | None = None,
    expected_status_code: int | None = None,
    validator_function: Callable | None = None,
) -> requests.Response:
    if expected_status_code is not None:
        assert test_response.status_code == expected_status_code, (
            f"Failed to assert response status code. Expected status code "
            f"'{expected_status_code}' but got status code {test_response.status_code}."
        )
    if expected_json_schema is not None:
        try:
            jsonschema.validate(test_response.json(), expected_json_schema)
        except jsonschema.exceptions.ValidationError as exc:
            pytest.fail(exc.message)
    if validator_function is not None:
        assert validator_function(
            test_response,
        ), f"Failed to assert response with custom validator function."

    return test_response


def get_all_listener_template_ids(admin_session: requests.Session) -> list[str]:
    return [
        listener_template["listener_template_id"]
        for listener_template in admin_session.get(
            "http://localhost:9999/api/listener-templates/all",
        ).json()
    ]


def get_all_listener_ids(admin_session: requests.Session) -> list[str]:
    return [
        listener["listener_id"]
        for listener in admin_session.get(
            "http://localhost:9999/api/listeners/all",
        ).json()
    ]


def get_all_user_account_ids(admin_session: requests.Session) -> list[str]:
    return [
        user_account["user_account_id"]
        for user_account in admin_session.get(
            "http://localhost:9999/api/user-accounts/all",
        ).json()
    ]


def get_all_agent_template_ids(
    admin_session: requests.Session,
) -> list[str]:
    return [
        agent_template["agent_template_id"]
        for agent_template in admin_session.get(
            "http://localhost:9999/api/agent-templates/all",
        ).json()
    ]
