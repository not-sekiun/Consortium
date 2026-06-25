import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.test_assets_api import (
    ALL_RESOURCES_JSON_SCHEMA,
    RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


async def test_get_all_artifacts(client):
    """All roles can GET /api/artifacts/all."""
    validate_response(
        test_response=await client.get("/api/artifacts/all"),
        expected_json_schema=ALL_RESOURCES_JSON_SCHEMA,
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
