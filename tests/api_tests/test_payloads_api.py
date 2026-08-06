import pytest

import consortium.server.server_singletons as server_singletons
from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.test_assets_api import RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


def _seed_payload(name: str, description: str) -> str:
    # No payload upload/create endpoint is exposed, so seed a payload directly on the
    # payloads repository (redirected to a throwaway directory for the test session)
    # with a `data` field that satisfies the persistent payload metadata contract. The
    # agent template reference does not need to resolve to a live template:
    # `resolved_agent_template` is nullable.
    resource = server_singletons.payloads_service._repository_service.create_file(
        content=b"payload content",
        name=name,
        description=description,
        data={
            "agent_template": {
                "label": "consortium.agents.mock_1",
                "name": "Mock Agent 1",
            },
            "build_parameters": {},
            "payload_data": {},
        },
    )
    return str(resource.resource_id)


# Full resolved agent template, matching AgentTemplateModel. This is what
# `resolved_agent_template` holds when the persistent reference resolves at read-time.
AGENT_TEMPLATE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_template_id": {"type": "string"},
        "label": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": "string"},
        "compatible_framework_version": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "agent_type": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "agent_capabilities": {"type": "object"},
            },
            "required": ["name", "agent_capabilities"],
        },
        "compatible_listener_types": {
            "type": "array",
            "items": {"type": "string"},
        },
        "options": {"type": "object"},
        "validating_function": {"type": ["string", "null"]},
    },
    "required": [
        "agent_template_id",
        "label",
        "name",
        "description",
        "version",
        "compatible_framework_version",
        "authors",
        "agent_type",
        "compatible_listener_types",
        "options",
        "validating_function",
    ],
}
PAYLOAD_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "resource_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "size": {"type": ["integer", "null"]},
        "exists_on_disk": {"type": "boolean"},
        "datetime_created": {"type": "string"},
        "datetime_modified": {"type": "string"},
        "md5_checksum": {"type": ["string", "null"]},
        "is_directory": {"type": "boolean"},
        "data": {
            "type": "object",
            "properties": {
                # Persistent point-in-time reference stored on disk. Only `label` and
                # `name` are persisted (the id can vary on restart).
                "agent_template": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["label", "name"],
                },
                "build_parameters": {"type": "object"},
                "payload_data": {"type": "object"},
                # Live read-time resolution of `agent_template`, `None` when the template
                # cannot be resolved.
                "resolved_agent_template": {
                    "oneOf": [AGENT_TEMPLATE_JSON_SCHEMA, {"type": "null"}],
                },
            },
            "required": [
                "agent_template",
                "build_parameters",
                "payload_data",
                "resolved_agent_template",
            ],
        },
    },
    "required": [
        "resource_id",
        "name",
        "description",
        "size",
        "exists_on_disk",
        "datetime_created",
        "datetime_modified",
        "md5_checksum",
        "is_directory",
        "data",
    ],
}
ALL_PAYLOADS_JSON_SCHEMA = {
    "type": "array",
    "items": PAYLOAD_JSON_SCHEMA,
}


async def test_get_all_payloads(client):
    """All roles can GET /api/payloads/all."""
    validate_response(
        test_response=await client.get("/api/payloads/all"),
        expected_json_schema=ALL_PAYLOADS_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_payload_by_invalid_id_returns_404(client):
    """GET /api/payloads/{id} with unknown valid UUID4 returns 404 for all roles."""
    fake_uuid = "00000000-0000-4000-8000-000000000040"
    validate_response(
        test_response=await client.get(f"/api/payloads/{fake_uuid}"),
        expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_payload_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """DELETE /api/payloads/{id} returns 403 for spectators, 404 for admin/operator."""
    fake_uuid = "00000000-0000-4000-8000-000000000041"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.delete(f"/api/payloads/{fake_uuid}"),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.delete(f"/api/payloads/{fake_uuid}"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_download_payload_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """GET /api/payloads/download/{id} returns 403 for spectators, 404 for others."""
    fake_uuid = "00000000-0000-4000-8000-000000000042"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.get(f"/api/payloads/download/{fake_uuid}"),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.get(f"/api/payloads/download/{fake_uuid}"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_update_payload_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """PATCH /api/payloads/{id} returns 403 for spectators, 404 for admin/operator."""
    fake_uuid = "00000000-0000-4000-8000-000000000043"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.patch(
                f"/api/payloads/{fake_uuid}", json={"name": "new-name"}
            ),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.patch(
                f"/api/payloads/{fake_uuid}", json={"name": "new-name"}
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_update_payload_by_invalid_uuid_returns_422(admin_client):
    """PATCH /api/payloads/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.patch(
            "/api/payloads/not-a-uuid", json={"name": "new-name"}
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_update_payload_updates_name_and_description(admin_client):
    """PATCH /api/payloads/{id} updates the payload's name and description."""
    payload_id = _seed_payload(name="original", description="original description")

    response = await admin_client.patch(
        f"/api/payloads/{payload_id}",
        json={"name": "renamed", "description": "an updated description"},
    )
    validate_response(
        test_response=response,
        expected_json_schema=PAYLOAD_JSON_SCHEMA,
        expected_status_code=200,
    )
    body = response.json()
    assert body["name"] == "renamed"
    assert body["description"] == "an updated description"

    await admin_client.delete(f"/api/payloads/{payload_id}")


async def test_update_payload_does_not_update_data_over_endpoint(admin_client):
    """PATCH /api/payloads/{id} ignores a `data` field: only name/description mutable."""
    payload_id = _seed_payload(name="original", description="original description")

    response = await admin_client.patch(
        f"/api/payloads/{payload_id}",
        json={
            "name": "renamed",
            "data": {
                "agent_template": {"label": "spoofed", "name": "spoofed"},
                "build_parameters": {"spoofed": True},
                "payload_data": {"spoofed": True},
            },
        },
    )
    validate_response(
        test_response=response,
        expected_json_schema=PAYLOAD_JSON_SCHEMA,
        expected_status_code=200,
    )
    body = response.json()
    assert body["name"] == "renamed"
    # The `data` field from the request body is ignored: the stored metadata is
    # unchanged from what was recorded at creation.
    assert body["data"]["agent_template"] == {
        "label": "consortium.agents.mock_1",
        "name": "Mock Agent 1",
    }
    assert body["data"]["build_parameters"] == {}
    assert body["data"]["payload_data"] == {}

    await admin_client.delete(f"/api/payloads/{payload_id}")


async def test_get_payload_by_invalid_uuid_returns_422(admin_client):
    """GET /api/payloads/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/payloads/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_delete_payload_by_invalid_uuid_returns_422(admin_client):
    """DELETE /api/payloads/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.delete("/api/payloads/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_download_payload_by_invalid_uuid_returns_422(admin_client):
    """GET /api/payloads/download/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/payloads/download/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )
