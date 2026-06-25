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


async def test_get_all_payloads(client):
    """All roles can GET /api/payloads/all."""
    validate_response(
        test_response=await client.get("/api/payloads/all"),
        expected_json_schema=ALL_RESOURCES_JSON_SCHEMA,
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
