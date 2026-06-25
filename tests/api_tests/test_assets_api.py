import io

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

REPOSITORY_RESOURCE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "resource_id": {"type": "string"},
        "name": {"type": ["string", "null"]},
        "description": {"type": "string"},
        "size": {"type": ["integer", "null"]},
        "exists_on_disk": {"type": "boolean"},
        "datetime_created": {"type": "string"},
        "datetime_modified": {"type": "string"},
        "md5_checksum": {"type": ["string", "null"]},
        "is_directory": {"type": "boolean"},
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
    ],
}
ALL_RESOURCES_JSON_SCHEMA = {
    "type": "array",
    "items": REPOSITORY_RESOURCE_JSON_SCHEMA,
}
RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["REPOSITORY_RESOURCE_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


async def test_get_all_assets(client):
    """All roles can GET /api/assets/all."""
    validate_response(
        test_response=await client.get("/api/assets/all"),
        expected_json_schema=ALL_RESOURCES_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_asset_by_invalid_id_returns_404(
    admin_client, operator_client, client
):
    """GET /api/assets/{id} with unknown valid UUID4 returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000020"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.get(f"/api/assets/{fake_uuid}"),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        # Spectator has READ_ASSET_BY_ASSET_ID permission
        validate_response(
            test_response=await client.get(f"/api/assets/{fake_uuid}"),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )


async def test_delete_asset_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """DELETE /api/assets/{id} returns 403 for spectators, 404 for admin/operator."""
    fake_uuid = "00000000-0000-4000-8000-000000000021"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.delete(f"/api/assets/{fake_uuid}"),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.delete(f"/api/assets/{fake_uuid}"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_download_asset_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """GET /api/assets/download/{id} returns 403 for spectators, 404 for others."""
    fake_uuid = "00000000-0000-4000-8000-000000000022"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.get(f"/api/assets/download/{fake_uuid}"),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.get(f"/api/assets/download/{fake_uuid}"),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_get_asset_by_invalid_uuid_returns_422(admin_client):
    """GET /api/assets/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/assets/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_delete_asset_by_invalid_uuid_returns_422(admin_client):
    """DELETE /api/assets/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.delete("/api/assets/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_download_asset_by_invalid_uuid_returns_422(admin_client):
    """GET /api/assets/download/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/assets/download/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_upload_asset_requires_admin_or_operator(
    admin_client, operator_client, spectator_client, client
):
    """POST /api/assets/upload returns 403 for spectators."""
    if client == spectator_client:
        validate_response(
            test_response=await client.post(
                "/api/assets/upload",
                files={"file": ("test.txt", io.BytesIO(b"test"), "text/plain")},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )
