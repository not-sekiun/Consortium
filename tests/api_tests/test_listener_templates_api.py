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
MISSING_REQUIRED_OPTION_ERROR_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["MISSING_REQUIRED_LISTENER_TEMPLATE_OPTION_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {
                    "type": "object",
                    "properties": {
                        "listener_template_str": {"type": "string"},
                        "option_name": {"type": "string"},
                    },
                    "required": ["listener_template_str", "option_name"],
                },
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
OPTION_VALUE_ERROR_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["LISTENER_TEMPLATE_OPTION_VALUE_VALIDATION_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {
                    "type": "object",
                    "properties": {
                        "option_name": {"type": "string"},
                        "option_value": {},
                        "error_message": {"type": "string"},
                    },
                    "required": [
                        "option_name",
                        "option_value",
                        "error_message",
                    ],
                },
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


@pytest.mark.usefixtures("delete_listeners_after_test")
def test_create_listener_with_missing_required_option(
    admin_session: requests.Session,
):
    for listener_template_id in get_all_listener_template_ids(admin_session):
        listener_template = admin_session.get(
            f"http://localhost:9999/api/listener-templates/{listener_template_id}",
        ).json()

        # Find required options
        required_options = [
            option_name
            for option_name, option in listener_template["options"].items()
            if option["required"]
        ]

        if required_options:
            # Build parameters dict with all defaults except one required option
            parameters = {
                option_name: option["default_value"]
                for option_name, option in listener_template["options"].items()
            }
            # Remove one required option
            del parameters[required_options[0]]

            validate_response(
                test_response=admin_session.post(
                    f"http://localhost:9999/api/listener-templates/{listener_template_id}",
                    json=parameters,
                ),
                expected_json_schema=MISSING_REQUIRED_OPTION_ERROR_RESPONSE_JSON_SCHEMA,
                expected_status_code=422,
            )


@pytest.mark.usefixtures("delete_listeners_after_test")
def test_create_listener_with_invalid_option_value_type(
    admin_session: requests.Session,
):
    # Map of type names to invalid values
    invalid_values_by_type = {
        "str": 123,  # int instead of str
        "int": "not_an_int",  # str instead of int
        "float": "not_a_float",  # str instead of float
        "bool": "not_a_bool",  # str instead of bool
    }

    for listener_template_id in get_all_listener_template_ids(admin_session):
        listener_template = admin_session.get(
            f"http://localhost:9999/api/listener-templates/{listener_template_id}",
        ).json()

        # Build base parameters with all defaults
        parameters = {
            option_name: option["default_value"]
            for option_name, option in listener_template["options"].items()
        }

        # Find an option with a specific value_type to test invalid type
        for option_name, option in listener_template["options"].items():
            value_type = option.get("value_type")
            if value_type and value_type in invalid_values_by_type:
                # Create a copy with an invalid value for this option
                invalid_parameters = parameters.copy()
                invalid_parameters[option_name] = invalid_values_by_type[value_type]

                validate_response(
                    test_response=admin_session.post(
                        f"http://localhost:9999/api/listener-templates/{listener_template_id}",
                        json=invalid_parameters,
                    ),
                    expected_json_schema=OPTION_VALUE_ERROR_RESPONSE_JSON_SCHEMA,
                    expected_status_code=422,
                )
                # Only test one invalid option per template
                break
