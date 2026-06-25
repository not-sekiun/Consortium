import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    AGENT_GENERATOR_JSON_SCHEMA,
    AGENT_TEMPLATE_JSON_SCHEMA,
    AGENT_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
    ALL_AGENT_TEMPLATES_JSON_SCHEMA,
)
from tests.api_tests.utils import get_all_agent_template_ids, validate_response

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
    admin_client, spectator_client, client
):
    for template_id in await get_all_agent_template_ids(admin_client):
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
                    json=options_payload,
                ),
                expected_json_schema=AGENT_GENERATOR_JSON_SCHEMA,
                expected_status_code=201,
            )
        else:
            validate_response(
                test_response=await client.post(
                    f"/api/agent-templates/{template_id}",
                    json=options_payload,
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
