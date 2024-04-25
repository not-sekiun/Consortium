import pytest
import requests

from tests.common_json_response_schemas import FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA
from tests.test_agent_generators_api import AGENT_GENERATOR_RESPONSE_JSON_SCHEMA
from tests.utils import get_all_agent_template_ids, validate_response

AGENT_TEMPLATE_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "agent_type": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "compatible_listener_type_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "agent_type_id": {"type": "string"},
            },
            "required": ["name", "compatible_listener_type_ids", "agent_type_id"],
        },
        "authors": {"type": "array", "items": {"type": "string"}},
        "options": {"type": "object"},
        "agent_template_id": {"type": "string"},
        "validating_function": {"type": ["string", "null"]},
    },
    "required": [
        "name",
        "description",
        "agent_type",
        "authors",
        "options",
        "agent_template_id",
        "validating_function",
    ],
    "additionalProperties": False,
}
ALL_AGENT_TEMPLATES_RESPONSE_JSON_SCHEMA = {
    "type": "array",
    "items": AGENT_TEMPLATE_RESPONSE_JSON_SCHEMA,
}
AGENT_TEMPLATE_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_TEMPLATE_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


def test_get_all_agent_templates(
    session: requests.Session,
):
    validate_response(
        test_response=session.get(
            "http://localhost:9999/api/agent-templates/all",
        ),
        expected_json_schema=ALL_AGENT_TEMPLATES_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )


def test_get_agent_template_by_agent_template_id(
    admin_session: requests.Session,
    session: requests.Session,
):
    for agent_template_id in get_all_agent_template_ids(
        admin_session,
    ):
        validate_response(
            test_response=session.get(
                f"http://localhost:9999/api/agent-templates/{agent_template_id}",
            ),
            expected_json_schema=AGENT_TEMPLATE_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )

    validate_response(
        test_response=session.get(
            "http://localhost:9999/api/agent-templates/invalid-listener-template-id",
        ),
        expected_json_schema=AGENT_TEMPLATE_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
def test_create_agent_generator_through_agent_template_by_agent_template_id(
    admin_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    if session != spectator_session:
        # Test for admin sessions and operator sessions.
        for agent_template_id in get_all_agent_template_ids(admin_session):
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/agent-templates/{agent_template_id}",
                    json={
                        option_name: option["default_value"]
                        for option_name, option in session.get(
                            f"http://localhost:9999/api/agent-templates/{agent_template_id}",
                        )
                        .json()["options"]
                        .items()
                    },
                ),
                expected_json_schema=AGENT_GENERATOR_RESPONSE_JSON_SCHEMA,
                expected_status_code=201,
            )
    else:
        # Test for spectator sessions.
        for agent_template_id in get_all_agent_template_ids(admin_session):
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/agent-templates/{agent_template_id}",
                    json={
                        option_name: option["default_value"]
                        for option_name, option in session.get(
                            f"http://localhost:9999/api/agent-templates/{agent_template_id}",
                        )
                        .json()["options"]
                        .items()
                    },
                ),
                expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
                expected_status_code=403,
            )
