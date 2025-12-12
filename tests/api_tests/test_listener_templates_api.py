import pytest
import requests

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
)
from tests.api_tests.test_listeners_api import LISTENER_RESPONSE_JSON_SCHEMA
from tests.api_tests.utils import get_all_listener_template_ids, validate_response

LISTENER_TEMPLATE_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": "string"},
        "compatible_framework_version": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "listener_template_id": {"type": "string"},
        "listener_type": {
            "type": "object",
            "properties": {
                "listener_type_id": {"type": "string"},
                "name": {"type": "string"},
                "compatible_agent_types": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "agent_type_id": {"type": "string"},
                            "name": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["listener_type_id", "name", "compatible_agent_types"],
            "additionalProperties": False,
        },
        "options": {"type": "object"},
        "validating_function": {"type": ["string", "null"]},
    },
    "required": [
        "label",
        "name",
        "description",
        "version",
        "compatible_framework_version",
        "authors",
        "listener_template_id",
        "listener_type",
        "options",
        "validating_function",
    ],
    "additionalProperties": False,
}
ALL_LISTENER_TEMPLATES_RESPONSE_JSON_SCHEMA = {
    "type": "array",
    "items": LISTENER_TEMPLATE_RESPONSE_JSON_SCHEMA,
}
LISTENER_TEMPLATE_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["LISTENER_TEMPLATE_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


def test_get_all_listener_templates(
    session: requests.Session,
):
    validate_response(
        test_response=session.get(
            "http://localhost:9999/api/listener-templates/all",
        ),
        expected_json_schema=ALL_LISTENER_TEMPLATES_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )


def test_get_listener_template_by_listener_template_id(
    admin_session: requests.Session,
    session: requests.Session,
):
    for listener_template_id in get_all_listener_template_ids(admin_session):
        validate_response(
            test_response=session.get(
                f"http://localhost:9999/api/listener-templates/{listener_template_id}",
            ),
            expected_json_schema=LISTENER_TEMPLATE_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )

    validate_response(
        test_response=session.get(
            "http://localhost:9999/api/listener-templates/invalid-listener-template-id",
        ),
        expected_json_schema=LISTENER_TEMPLATE_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_listeners_after_test")
def test_create_listener_through_listener_template_by_listener_template_id(
    admin_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    if session != spectator_session:
        # Test for admin sessions and operator sessions.
        for listener_template_id in get_all_listener_template_ids(admin_session):
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/listener-templates/{listener_template_id}",
                    json={
                        option_name: option["default_value"]
                        for option_name, option in session.get(
                            f"http://localhost:9999/api/listener-templates/{listener_template_id}",
                        )
                        .json()["options"]
                        .items()
                    },
                ),
                expected_json_schema=LISTENER_RESPONSE_JSON_SCHEMA,
                expected_status_code=201,
            )
    else:
        # Test for spectator sessions.
        for listener_template_id in get_all_listener_template_ids(admin_session):
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/listener-templates/{listener_template_id}",
                    json={
                        option_name: option["default_value"]
                        for option_name, option in session.get(
                            f"http://localhost:9999/api/listener-templates/{listener_template_id}",
                        )
                        .json()["options"]
                        .items()
                    },
                ),
                expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
                expected_status_code=403,
            )
