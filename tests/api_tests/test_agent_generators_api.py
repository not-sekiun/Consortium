import uuid

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
    SUCCESS_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    AGENT_GENERATOR_JSON_SCHEMA,
)
from tests.api_tests.utils import (
    get_all_agent_template_ids,
    validate_response,
)

pytestmark = pytest.mark.anyio

ALL_AGENT_GENERATORS_JSON_SCHEMA = {
    "type": "array",
    "items": AGENT_GENERATOR_JSON_SCHEMA,
}
AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_GENERATOR_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
AGENT_GENERATOR_ALREADY_RUNNING_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_GENERATOR_ALREADY_RUNNING_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
AGENT_GENERATOR_NOT_RUNNING_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_GENERATOR_NOT_RUNNING_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


async def _create_one_agent_generator_per_template(
    admin_client,
) -> list[str]:
    """Create one agent generator per available template; return created IDs."""
    agent_generator_ids = []
    for template_id in await get_all_agent_template_ids(admin_client):
        template = (
            await admin_client.get(f"/api/agent-templates/{template_id}")
        ).json()
        options_payload = {
            name: opt["default_value"] for name, opt in template["options"].items()
        }
        response = await admin_client.post(
            f"/api/agent-templates/{template_id}",
            json=options_payload,
        )
        if response.status_code == 201:
            agent_generator_ids.append(response.json()["agent_generator_id"])
    return agent_generator_ids


async def test_get_all_agent_generators_empty(client):
    """GET /api/agent-generators/all returns an empty list when none exist."""
    validate_response(
        test_response=await client.get("/api/agent-generators/all"),
        expected_json_schema=ALL_AGENT_GENERATORS_JSON_SCHEMA,
        expected_status_code=200,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_get_all_agent_generators(admin_client, client):
    await _create_one_agent_generator_per_template(admin_client)
    validate_response(
        test_response=await client.get("/api/agent-generators/all"),
        expected_json_schema=ALL_AGENT_GENERATORS_JSON_SCHEMA,
        expected_status_code=200,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_get_agent_generator_by_agent_generator_id(admin_client, client):
    ag_ids = await _create_one_agent_generator_per_template(admin_client)
    for ag_id in ag_ids:
        validate_response(
            test_response=await client.get(f"/api/agent-generators/{ag_id}"),
            expected_json_schema=AGENT_GENERATOR_JSON_SCHEMA,
            expected_status_code=200,
        )


async def test_get_agent_generator_by_invalid_id_returns_404(admin_client):
    """A valid UUID4 that does not match any agent generator returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000002"
    validate_response(
        test_response=await admin_client.get(f"/api/agent-generators/{fake_uuid}"),
        expected_json_schema=AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_start_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client
):
    ag_ids = await _create_one_agent_generator_per_template(admin_client)
    for ag_id in ag_ids:
        if client != spectator_client:
            validate_response(
                test_response=await client.post(f"/api/agent-generators/{ag_id}/start"),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
            await admin_client.post(f"/api/agent-generators/{ag_id}/stop")
        else:
            validate_response(
                test_response=await client.post(f"/api/agent-generators/{ag_id}/start"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_start_agent_generator_already_running_returns_409(admin_client):
    """Starting an already-running agent generator returns 409."""
    ag_ids = await _create_one_agent_generator_per_template(admin_client)
    for ag_id in ag_ids:
        await admin_client.post(f"/api/agent-generators/{ag_id}/start")
        validate_response(
            test_response=await admin_client.post(
                f"/api/agent-generators/{ag_id}/start"
            ),
            expected_json_schema=AGENT_GENERATOR_ALREADY_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )
        await admin_client.post(f"/api/agent-generators/{ag_id}/stop")


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_stop_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client
):
    ag_ids = await _create_one_agent_generator_per_template(admin_client)
    for ag_id in ag_ids:
        if client != spectator_client:
            await admin_client.post(f"/api/agent-generators/{ag_id}/start")
            validate_response(
                test_response=await client.post(f"/api/agent-generators/{ag_id}/stop"),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
        else:
            await admin_client.post(f"/api/agent-generators/{ag_id}/start")
            validate_response(
                test_response=await client.post(f"/api/agent-generators/{ag_id}/stop"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.post(f"/api/agent-generators/{ag_id}/stop")


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_stop_agent_generator_not_running_returns_409(admin_client):
    """Stopping an agent generator that is not running returns 409."""
    ag_ids = await _create_one_agent_generator_per_template(admin_client)
    for ag_id in ag_ids:
        validate_response(
            test_response=await admin_client.post(
                f"/api/agent-generators/{ag_id}/stop"
            ),
            expected_json_schema=AGENT_GENERATOR_NOT_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_cancel_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client
):
    ag_ids = await _create_one_agent_generator_per_template(admin_client)
    for ag_id in ag_ids:
        if client != spectator_client:
            await admin_client.post(f"/api/agent-generators/{ag_id}/start")
            validate_response(
                test_response=await client.post(
                    f"/api/agent-generators/{ag_id}/cancel"
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
        else:
            await admin_client.post(f"/api/agent-generators/{ag_id}/start")
            validate_response(
                test_response=await client.post(
                    f"/api/agent-generators/{ag_id}/cancel"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.post(f"/api/agent-generators/{ag_id}/cancel")


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_update_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client
):
    new_name = uuid.uuid4().hex
    new_description = uuid.uuid4().hex
    ag_ids = await _create_one_agent_generator_per_template(admin_client)
    for ag_id in ag_ids:
        if client != spectator_client:
            validate_response(
                test_response=await client.patch(
                    f"/api/agent-generators/{ag_id}",
                    json={"name": new_name, "description": new_description},
                ),
                expected_json_schema=AGENT_GENERATOR_JSON_SCHEMA,
                expected_status_code=200,
                validator_function=lambda r, n=new_name, d=new_description: (
                    r.json()["name"] == n and r.json()["description"] == d
                ),
            )
        else:
            validate_response(
                test_response=await client.patch(
                    f"/api/agent-generators/{ag_id}",
                    json={"name": new_name},
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_delete_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client
):
    ag_ids = await _create_one_agent_generator_per_template(admin_client)
    for ag_id in ag_ids:
        if client != spectator_client:
            validate_response(
                test_response=await client.delete(f"/api/agent-generators/{ag_id}"),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
        else:
            validate_response(
                test_response=await client.delete(f"/api/agent-generators/{ag_id}"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.delete(f"/api/agent-generators/{ag_id}")


async def test_delete_agent_generator_not_found(admin_client):
    """Deleting a non-existent agent generator returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000003"
    validate_response(
        test_response=await admin_client.delete(f"/api/agent-generators/{fake_uuid}"),
        expected_json_schema=AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_get_agent_generator_by_invalid_uuid_returns_422(admin_client):
    """GET /api/agent-generators/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/agent-generators/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_delete_agent_generator_by_invalid_uuid_returns_422(admin_client):
    """DELETE /api/agent-generators/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.delete("/api/agent-generators/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )
