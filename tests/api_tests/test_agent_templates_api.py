import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    AGENT_GENERATOR_JSON_SCHEMA,
    AGENT_TEMPLATE_JSON_SCHEMA,
    AGENT_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
    AGENT_TEMPLATE_OPTION_NOT_FOUND_ERROR_JSON_SCHEMA,
    AGENT_TEMPLATE_OPTION_VALUE_VALIDATION_ERROR_JSON_SCHEMA,
    ALL_AGENT_TEMPLATES_JSON_SCHEMA,
)
from tests.api_tests.utils import (
    build_create_request_body,
    create_agent_generator_from_template,
    get_all_agent_template_ids,
    validate_response,
)

pytestmark = pytest.mark.anyio


async def test_get_all_agent_templates(client):
    validate_response(
        test_response=await client.get("/api/agent-templates/all"),
        expected_json_schema=ALL_AGENT_TEMPLATES_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_agent_template_by_agent_template_id(admin_client, client):
    for template_id in await get_all_agent_template_ids(admin_client):
        validate_response(
            test_response=await client.get(f"/api/agent-templates/{template_id}"),
            expected_json_schema=AGENT_TEMPLATE_JSON_SCHEMA,
            expected_status_code=200,
        )

    # Non-UUID4 string: 422
    validate_response(
        test_response=await client.get(
            "/api/agent-templates/invalid-agent-template-id"
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )
    # Valid UUID4 that does not exist: 404
    validate_response(
        test_response=await client.get(
            "/api/agent-templates/00000000-0000-4000-8000-000000000060"
        ),
        expected_json_schema=AGENT_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_create_agent_generator_through_agent_template(
    admin_client, spectator_client, client, mock_agent_template_ids
):
    for template_id in mock_agent_template_ids:
        template = (
            await admin_client.get(f"/api/agent-templates/{template_id}")
        ).json()
        options_payload = {
            name: opt["default_value"] for name, opt in template["options"].items()
        }

        if client != spectator_client:
            validate_response(
                test_response=await client.post(
                    f"/api/agent-templates/{template_id}",
                    json=build_create_request_body(options=options_payload),
                ),
                expected_json_schema=AGENT_GENERATOR_JSON_SCHEMA,
                expected_status_code=201,
            )
        else:
            validate_response(
                test_response=await client.post(
                    f"/api/agent-templates/{template_id}",
                    json=build_create_request_body(options=options_payload),
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


async def test_create_agent_generator_with_nonexistent_template_id(admin_client):
    """POST /api/agent-templates/{id} with a valid UUID4 that has no matching template returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000063"
    validate_response(
        test_response=await admin_client.post(
            f"/api/agent-templates/{fake_uuid}",
            json=build_create_request_body(options={}),
        ),
        expected_json_schema=AGENT_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_create_agent_generator_with_unknown_option_key_returns_422(
    admin_client, mock_agent_template_ids
):
    """POST /api/agent-templates/{id} with an unrecognised option key returns 422."""
    for template_id in mock_agent_template_ids:
        validate_response(
            test_response=await admin_client.post(
                f"/api/agent-templates/{template_id}",
                json=build_create_request_body(
                    options={"nonexistent_option_key": "value"},
                ),
            ),
            expected_json_schema=AGENT_TEMPLATE_OPTION_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_create_agent_generator_with_invalid_option_value_type_returns_422(
    admin_client, mock_agent_template_ids
):
    """POST /api/agent-templates/{id} with a wrong-type value for a known option returns 422."""
    for template_id in mock_agent_template_ids:
        validate_response(
            test_response=await admin_client.post(
                f"/api/agent-templates/{template_id}",
                # retry_count is an int option; passing a string triggers the value error
                json=build_create_request_body(options={"retry_count": "not_an_int"}),
            ),
            expected_json_schema=AGENT_TEMPLATE_OPTION_VALUE_VALIDATION_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_create_agent_generator_with_explicit_name_and_description(
    admin_client, mock_agent_template_ids
):
    """An explicitly supplied name and description are used verbatim."""
    for template_id in mock_agent_template_ids:
        response = await create_agent_generator_from_template(
            admin_client=admin_client,
            agent_template_id=template_id,
            name="explicitly-named-generator",
            description="explicitly described generator",
        )
        assert response.status_code == 201, response.text
        agent_generator = response.json()
        assert agent_generator["name"] == "explicitly-named-generator"
        assert agent_generator["description"] == "explicitly described generator"


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_create_agent_generator_without_a_name_generates_one(
    admin_client, mock_agent_template_ids
):
    """Omitting the name leaves the server to generate a non-empty one."""
    for template_id in mock_agent_template_ids:
        response = await create_agent_generator_from_template(
            admin_client=admin_client,
            agent_template_id=template_id,
        )
        assert response.status_code == 201, response.text
        assert response.json()["name"], (
            "An agent generator created without an explicit name should have been "
            "given a generated one"
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_create_agent_generator_name_option_is_not_the_generator_name(
    admin_client, mock_agent_template_ids
):
    """A template option called "name" is an ordinary parameter, not the display name.

    Both mock agent templates declare an option called "name". Its value has to land in
    the agent generator's parameters and must never be picked up as the generator's
    name, whether or not an explicit name was supplied alongside it.
    """
    for template_id in mock_agent_template_ids:
        # No explicit name: the generated name must not come from the option
        response = await create_agent_generator_from_template(
            admin_client=admin_client,
            agent_template_id=template_id,
            option_overrides={"name": "value-of-the-name-option"},
        )
        assert response.status_code == 201, response.text
        agent_generator = response.json()
        assert agent_generator["parameters"]["name"] == "value-of-the-name-option"
        assert agent_generator["name"] != "value-of-the-name-option"

        # An explicit name alongside the option: the explicit name wins and the option
        # is left untouched
        response = await create_agent_generator_from_template(
            admin_client=admin_client,
            agent_template_id=template_id,
            option_overrides={"name": "value-of-the-name-option"},
            name="the-explicit-name",
        )
        assert response.status_code == 201, response.text
        agent_generator = response.json()
        assert agent_generator["parameters"]["name"] == "value-of-the-name-option"
        assert agent_generator["name"] == "the-explicit-name"
