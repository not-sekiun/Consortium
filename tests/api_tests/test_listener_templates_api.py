import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import (
    build_create_request_body,
    create_listener_from_template,
    get_all_listener_template_ids,
    validate_response,
)

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
                "name": {"type": "string"},
                "registered_compatible_agent_types": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["name", "registered_compatible_agent_types"],
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
                "detail": {"type": ["object", "null"]},
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
LISTENER_TEMPLATE_OPTION_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["LISTENER_TEMPLATE_OPTION_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {"type": ["object", "null"]},
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

    # Non-UUID4 string: 422
    validate_response(
        test_response=await client.get(
            "/api/listener-templates/invalid-listener-template-id"
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )
    # Valid UUID4 that does not exist: 404
    validate_response(
        test_response=await client.get(
            "/api/listener-templates/00000000-0000-4000-8000-000000000061"
        ),
        expected_json_schema=LISTENER_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_through_listener_template(
    admin_client, spectator_client, client, mock_listener_template_ids
):
    from tests.api_tests.test_listeners_api import LISTENER_JSON_SCHEMA

    for template_id in mock_listener_template_ids:
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
                    json=build_create_request_body(options=options_payload),
                ),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=201,
            )
        else:
            validate_response(
                test_response=await client.post(
                    f"/api/listener-templates/{template_id}",
                    json=build_create_request_body(options=options_payload),
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_invalid_template_id(admin_client):
    """POST /api/listener-templates/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.post(
            "/api/listener-templates/invalid-template-id",
            json=build_create_request_body(options={}),
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_nonexistent_template_id(admin_client):
    """POST /api/listener-templates/{id} with valid UUID4 that does not exist returns 404."""
    validate_response(
        test_response=await admin_client.post(
            "/api/listener-templates/00000000-0000-4000-8000-000000000062",
            json=build_create_request_body(options={}),
        ),
        expected_json_schema=LISTENER_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_missing_required_option(
    admin_client, mock_listener_template_ids
):
    for template_id in mock_listener_template_ids:
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
                    json=build_create_request_body(options=params),
                ),
                expected_json_schema=MISSING_REQUIRED_OPTION_ERROR_JSON_SCHEMA,
                expected_status_code=422,
            )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_invalid_option_value_type(
    admin_client, mock_listener_template_ids
):
    invalid_values_by_type = {
        "str": 123,
        "int": "not_an_int",
        "float": "not_a_float",
        "bool": "not_a_bool",
    }
    for template_id in mock_listener_template_ids:
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
                        json=build_create_request_body(options=invalid_params),
                    ),
                    expected_json_schema=OPTION_VALUE_ERROR_JSON_SCHEMA,
                    expected_status_code=422,
                )
                break


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_unknown_option_key_returns_422(
    admin_client, mock_listener_template_ids
):
    """POST /api/listener-templates/{id} with an unrecognised option key returns 422."""
    for template_id in mock_listener_template_ids:
        template = (
            await admin_client.get(f"/api/listener-templates/{template_id}")
        ).json()
        params = {
            name: opt["default_value"] for name, opt in template["options"].items()
        }
        params["nonexistent_option_key"] = "value"
        validate_response(
            test_response=await admin_client.post(
                f"/api/listener-templates/{template_id}",
                json=build_create_request_body(options=params),
            ),
            expected_json_schema=LISTENER_TEMPLATE_OPTION_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_with_explicit_name_and_description(
    admin_client, mock_listener_template_ids
):
    """An explicitly supplied name and description are used verbatim."""
    for template_id in mock_listener_template_ids:
        response = await create_listener_from_template(
            admin_client=admin_client,
            listener_template_id=template_id,
            name="explicitly-named-listener",
            description="explicitly described listener",
        )
        assert response.status_code == 201, response.text
        listener = response.json()
        assert listener["name"] == "explicitly-named-listener"
        assert listener["description"] == "explicitly described listener"


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_without_a_name_generates_one(
    admin_client, mock_listener_template_ids
):
    """Omitting the name leaves the server to generate a non-empty one."""
    for template_id in mock_listener_template_ids:
        response = await create_listener_from_template(
            admin_client=admin_client,
            listener_template_id=template_id,
        )
        assert response.status_code == 201, response.text
        assert response.json()["name"], (
            "A listener created without an explicit name should have been given a "
            "generated one"
        )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_create_listener_name_option_is_not_the_listener_name(
    admin_client, mock_listener_template_ids
):
    """A template option called "name" is an ordinary parameter, not the display name.

    Both mock listener templates declare an option called "name". Its value has to land
    in the listener's parameters and must never be picked up as the listener's name,
    whether or not an explicit name was supplied alongside it.
    """
    for template_id in mock_listener_template_ids:
        # No explicit name: the generated name must not come from the option
        response = await create_listener_from_template(
            admin_client=admin_client,
            listener_template_id=template_id,
            option_overrides={"name": "value-of-the-name-option"},
        )
        assert response.status_code == 201, response.text
        listener = response.json()
        assert listener["parameters"]["name"] == "value-of-the-name-option"
        assert listener["name"] != "value-of-the-name-option"

        # An explicit name alongside the option: the explicit name wins and the option
        # is left untouched
        response = await create_listener_from_template(
            admin_client=admin_client,
            listener_template_id=template_id,
            option_overrides={"name": "value-of-the-name-option"},
            name="the-explicit-name",
        )
        assert response.status_code == 201, response.text
        listener = response.json()
        assert listener["parameters"]["name"] == "value-of-the-name-option"
        assert listener["name"] == "the-explicit-name"
