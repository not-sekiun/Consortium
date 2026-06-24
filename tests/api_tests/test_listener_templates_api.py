import pytest

from tests.api_tests.common_json_response_schemas import FORBIDDEN_ERROR_JSON_SCHEMA
from tests.api_tests.utils import get_all_listener_template_ids, validate_response

pytestmark = pytest.mark.anyio

LISTENER_TEMPLATE_JSON_SCHEMA = {
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
ALL_LISTENER_TEMPLATES_JSON_SCHEMA = {
    "type": "array",
    "items": LISTENER_TEMPLATE_JSON_SCHEMA,
}
LISTENER_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA = {
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
MISSING_REQUIRED_OPTION_ERROR_JSON_SCHEMA = {
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
                        "option_str": {"type": "string"},
                    },
                    "required": ["listener_template_str", "option_str"],
                },
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
OPTION_VALUE_ERROR_JSON_SCHEMA = {
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
                        "option_str": {"type": "string"},
                        "option_value": {},
                        "error_message": {"type": "string"},
                    },
                    "required": ["option_str", "option_value", "error_message"],
                },
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


async def test_get_all_listener_templates(client):
    validate_response(
        test_response=await client.get("/api/listener-templates/all"),
        expected_json_schema=ALL_LISTENER_TEMPLATES_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_listener_template_by_listener_template_id(admin_client, client):
    for template_id in await get_all_listener_template_ids(admin_client):
        validate_response(
            test_response=await client.get(f"/api/listener-templates/{template_id}"),
            expected_json_schema=LISTENER_TEMPLATE_JSON_SCHEMA,
            expected_status_code=200,
        )

    validate_response(
        test_response=await client.get(
            "/api/listener-templates/invalid-listener-template-id"
        ),
        expected_json_schema=LISTENER_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_through_listener_template(
    admin_client, spectator_client, client
):
    from tests.api_tests.test_listeners_api import LISTENER_JSON_SCHEMA

    for template_id in await get_all_listener_template_ids(admin_client):
        template = (
            await admin_client.get(f"/api/listener-templates/{template_id}")
        ).json()
        options_payload = {
            name: opt["default_value"] for name, opt in template["options"].items()
        }

        if client != spectator_client:
            validate_response(
                test_response=await client.post(
                    f"/api/listener-templates/{template_id}",
                    json=options_payload,
                ),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=201,
            )
        else:
            validate_response(
                test_response=await client.post(
                    f"/api/listener-templates/{template_id}",
                    json=options_payload,
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_invalid_template_id(admin_client):
    validate_response(
        test_response=await admin_client.post(
            "/api/listener-templates/invalid-template-id",
            json={},
        ),
        expected_json_schema=LISTENER_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_missing_required_option(admin_client):
    for template_id in await get_all_listener_template_ids(admin_client):
        template = (
            await admin_client.get(f"/api/listener-templates/{template_id}")
        ).json()
        required_options = [
            name for name, opt in template["options"].items() if opt["required"]
        ]
        if required_options:
            params = {
                name: opt["default_value"] for name, opt in template["options"].items()
            }
            del params[required_options[0]]
            validate_response(
                test_response=await admin_client.post(
                    f"/api/listener-templates/{template_id}",
                    json=params,
                ),
                expected_json_schema=MISSING_REQUIRED_OPTION_ERROR_JSON_SCHEMA,
                expected_status_code=422,
            )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_invalid_option_value_type(admin_client):
    invalid_values_by_type = {
        "str": 123,
        "int": "not_an_int",
        "float": "not_a_float",
        "bool": "not_a_bool",
    }
    for template_id in await get_all_listener_template_ids(admin_client):
        template = (
            await admin_client.get(f"/api/listener-templates/{template_id}")
        ).json()
        params = {
            name: opt["default_value"] for name, opt in template["options"].items()
        }
        for option_name, option in template["options"].items():
            value_type = option.get("value_type")
            if value_type and value_type in invalid_values_by_type:
                invalid_params = params.copy()
                invalid_params[option_name] = invalid_values_by_type[value_type]
                validate_response(
                    test_response=await admin_client.post(
                        f"/api/listener-templates/{template_id}",
                        json=invalid_params,
                    ),
                    expected_json_schema=OPTION_VALUE_ERROR_JSON_SCHEMA,
                    expected_status_code=422,
                )
                break
