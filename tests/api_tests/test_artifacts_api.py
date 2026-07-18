import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.test_assets_api import RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

# Full resolved agent, matching AgentModel. This is what `resolved_agent` holds when the
# persistent `agent` reference resolves at read-time.
AGENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "endpoint": {"type": "string"},
        "agent_type": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "agent_capabilities": {"type": "object"},
            },
            "required": ["name", "agent_capabilities"],
        },
        "user": {"type": ["string", "null"]},
        "is_admin": {"type": ["boolean", "null"]},
        "os": {"type": ["string", "null"]},
        "version": {"type": ["string", "null"]},
        "arch": {"type": ["string", "null"]},
        "pid": {"type": ["integer", "null"]},
        "locale": {"type": ["string", "null"]},
        "remote_ip": {"type": ["string", "null"]},
        "local_ip": {"type": ["string", "null"]},
        "hostname": {"type": ["string", "null"]},
        "datetime_first_checked_in": {"type": "string"},
        "datetime_last_checked_in": {"type": "string"},
        "status": {"type": "string"},
        "connected_listener": {
            "type": ["object", "null"],
            "properties": {
                "listener_id": {"type": "string"},
                "name": {"type": "string"},
            },
        },
        "agent_data": {"type": ["object", "null"]},
    },
    "required": [
        "agent_id",
        "name",
        "description",
        "endpoint",
        "agent_type",
        "user",
        "is_admin",
        "os",
        "version",
        "arch",
        "pid",
        "locale",
        "remote_ip",
        "local_ip",
        "hostname",
        "datetime_first_checked_in",
        "datetime_last_checked_in",
        "status",
        "connected_listener",
        "agent_data",
    ],
}
ARTIFACT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "resource_id": {"type": "string"},
        "name": {"type": ["string", "null"]},
        "description": {"type": "string"},
        "size": {"type": ["integer", "null"]},
        "extension": {"type": ["string", "null"]},
        "exists_on_disk": {"type": "boolean"},
        "datetime_created": {"type": "string"},
        "datetime_modified": {"type": "string"},
        "md5_checksum": {"type": ["string", "null"]},
        "is_directory": {"type": "boolean"},
        "data": {
            "type": "object",
            "properties": {
                # Persistent point-in-time reference to the producing agent recorded at
                # creation, `None` when the artifact was created without agent
                # attribution.
                "agent": {
                    "type": ["object", "null"],
                    "properties": {
                        "agent_id": {"type": "string"},
                        "name": {"type": "string"},
                        "agent_type": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "agent_capabilities": {"type": "object"},
                            },
                            "required": ["name", "agent_capabilities"],
                        },
                    },
                },
                # Live read-time resolution of `agent`, `None` when the producing agent
                # cannot be resolved.
                "resolved_agent": {
                    "oneOf": [AGENT_JSON_SCHEMA, {"type": "null"}],
                },
            },
            "required": ["agent", "resolved_agent"],
        },
    },
    "required": [
        "resource_id",
        "name",
        "description",
        "size",
        "extension",
        "exists_on_disk",
        "datetime_created",
        "datetime_modified",
        "md5_checksum",
        "is_directory",
        "data",
    ],
}
ALL_ARTIFACTS_JSON_SCHEMA = {
    "type": "array",
    "items": ARTIFACT_JSON_SCHEMA,
}


async def test_get_all_artifacts(client):
    """All roles can GET /api/artifacts/all."""
    validate_response(
        test_response=await client.get("/api/artifacts/all"),
        expected_json_schema=ALL_ARTIFACTS_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_artifact_by_invalid_id_returns_404(client):
    """GET /api/artifacts/{id} with unknown valid UUID4 returns 404 for all roles."""
    fake_uuid = "00000000-0000-4000-8000-000000000030"
    validate_response(
        test_response=await client.get(f"/api/artifacts/{fake_uuid}"),
        expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_artifact_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """DELETE /api/artifacts/{id} returns 403 for spectators, 404 for admin/operator."""
    fake_uuid = "00000000-0000-4000-8000-000000000031"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.delete(f"/api/artifacts/{fake_uuid}"),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.delete(f"/api/artifacts/{fake_uuid}"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_download_artifact_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """GET /api/artifacts/download/{id} returns 403 for spectators, 404 for others."""
    fake_uuid = "00000000-0000-4000-8000-000000000032"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.get(f"/api/artifacts/download/{fake_uuid}"),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.get(f"/api/artifacts/download/{fake_uuid}"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_get_artifact_by_invalid_uuid_returns_422(admin_client):
    """GET /api/artifacts/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/artifacts/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_delete_artifact_by_invalid_uuid_returns_422(admin_client):
    """DELETE /api/artifacts/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.delete("/api/artifacts/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_download_artifact_by_invalid_uuid_returns_422(admin_client):
    """GET /api/artifacts/download/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/artifacts/download/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )
