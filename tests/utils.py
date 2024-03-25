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
        assert test_response.status_code == expected_status_code
    if expected_json_schema is not None:
        try:
            jsonschema.validate(test_response.json(), expected_json_schema)
        except jsonschema.exceptions.ValidationError as exc:
            pytest.fail(exc.message)
    if validator_function is not None:
        assert validator_function(test_response)

    return test_response


def create_listeners(
    num_listeners: int,
    listener_template_endpoint: str,
    admin_session: requests.Session,
) -> list[str]:
    listener_ids = []
    for i in range(num_listeners):
        listener = admin_session.post(
            listener_template_endpoint,
            json={
                option_name: option["default_value"]
                for option_name, option in admin_session.get(
                    listener_template_endpoint,
                )
                .json()["options"]
                .items()
            },
        )
        listner_ids.append(listener["listener_id"])
    return listener_ids


def delete_all_listeners(admin_session: requests.Session):
    all_listener_ids = [
        listener["listener_id"]
        for listener in admin_session.get(
            "http://localhost:9999/api/listeners/all",
        ).json()
    ]
    for listener_id in all_listener_ids:
        admin_session.delete(f"http://localhost:9999/api/listeners/{listener_id}")
