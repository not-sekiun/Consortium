import pytest

import consortium.server.server_singletons as server_singletons
from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    ALL_ARTIFACTS_JSON_SCHEMA,
    ARTIFACT_JSON_SCHEMA,
    RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

# Full resolved agent, matching AgentModel. This is what `resolved_agent` holds when the
# persistent `agent` reference resolves at read-time.


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


async def test_update_artifact_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """PATCH /api/artifacts/{id} returns 403 for spectators, 404 for admin/operator."""
    fake_uuid = "00000000-0000-4000-8000-000000000033"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.patch(
                f"/api/artifacts/{fake_uuid}", json={"name": "new-name"}
            ),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.patch(
                f"/api/artifacts/{fake_uuid}", json={"name": "new-name"}
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_update_artifact_by_invalid_uuid_returns_422(admin_client):
    """PATCH /api/artifacts/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.patch(
            "/api/artifacts/not-a-uuid", json={"name": "new-name"}
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_update_artifact_updates_name_and_description(admin_client):
    """PATCH /api/artifacts/{id} updates the artifact's name and description."""
    # No artifact upload endpoint is exposed, so seed one through the service. The
    # artifacts repository is redirected to a throwaway directory for the test session.
    artifact = await server_singletons.artifacts_service.create_artifact_file(
        content=b"artifact content",
        name="original",
        description="original description",
    )
    artifact_id = artifact.to_json()["resource_id"]

    response = await admin_client.patch(
        f"/api/artifacts/{artifact_id}",
        json={"name": "renamed", "description": "an updated description"},
    )
    validate_response(
        test_response=response,
        expected_json_schema=ARTIFACT_JSON_SCHEMA,
        expected_status_code=200,
    )
    body = response.json()
    assert body["name"] == "renamed"
    assert body["description"] == "an updated description"

    await admin_client.delete(f"/api/artifacts/{artifact_id}")


async def test_update_artifact_does_not_update_data_over_endpoint(admin_client):
    """PATCH /api/artifacts/{id} ignores a `data` field: only name/description mutable."""
    artifact = await server_singletons.artifacts_service.create_artifact_file(
        content=b"artifact content",
        name="original",
        description="original description",
    )
    artifact_json = artifact.to_json()
    artifact_id = artifact_json["resource_id"]
    original_agent = artifact_json["data"]["agent"]

    response = await admin_client.patch(
        f"/api/artifacts/{artifact_id}",
        json={
            "name": "renamed",
            "data": {"agent": {"agent_id": "spoofed", "name": "spoofed"}},
        },
    )
    validate_response(
        test_response=response,
        expected_json_schema=ARTIFACT_JSON_SCHEMA,
        expected_status_code=200,
    )
    body = response.json()
    assert body["name"] == "renamed"
    # The `data` field from the request body is ignored: the stored attribution is
    # unchanged from what was recorded at creation.
    assert body["data"]["agent"] == original_agent

    await admin_client.delete(f"/api/artifacts/{artifact_id}")


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
