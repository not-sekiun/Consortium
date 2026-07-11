import io

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

ASSET_JSON_SCHEMA = {
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
                "user_account": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "role": {"type": "string"},
                    },
                    "required": ["username", "role"],
                },
                "resolved_user_account": {
                    "type": ["object", "null"],
                    "properties": {
                        "user_account_id": {"type": "string"},
                        "username": {"type": "string"},
                        "role": {"type": "string"},
                    },
                },
            },
            "required": ["user_account", "resolved_user_account"],
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
ALL_RESOURCES_JSON_SCHEMA = {
    "type": "array",
    "items": ASSET_JSON_SCHEMA,
}
RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["RESOURCE_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
DIRECTORY_ARCHIVE_FORMAT_NOT_SPECIFIED_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": [
                        "REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_NOT_SPECIFIED_ERROR"
                    ],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
DIRECTORY_FILE_NOT_ARCHIVE_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["REPOSITORY_DIRECTORY_FILE_NOT_ARCHIVE_FILE_ERROR"],
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


async def test_upload_file_asset_returns_200(admin_client):
    """POST /api/assets/upload with a regular file and is_directory=false returns 200."""
    response = await admin_client.post(
        "/api/assets/upload",
        data={"is_directory": "false"},
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    validate_response(
        test_response=response,
        expected_json_schema=ASSET_JSON_SCHEMA,
        expected_status_code=200,
    )
    asset_id = response.json()["resource_id"]
    await admin_client.delete(f"/api/assets/{asset_id}")


async def test_upload_directory_asset_without_extension_returns_415(admin_client):
    """POST /api/assets/upload with is_directory=true and no file extension returns 415.

    os.path.splitext on a filename with no extension yields an empty extension
    string, which triggers RepositoryDirectoryArchiveFileFormatNotSpecifiedError.
    """
    validate_response(
        test_response=await admin_client.post(
            "/api/assets/upload",
            data={"is_directory": "true"},
            files={
                "file": (
                    "testfile",
                    io.BytesIO(b"archive content"),
                    "application/octet-stream",
                )
            },
        ),
        expected_json_schema=DIRECTORY_ARCHIVE_FORMAT_NOT_SPECIFIED_ERROR_JSON_SCHEMA,
        expected_status_code=415,
    )


async def test_upload_directory_asset_with_non_archive_extension_returns_415(
    admin_client,
):
    """POST /api/assets/upload with is_directory=true and a non-archive extension returns 415.

    A .txt extension is not in the allowed archive set (.zip, .tar, .gz, .bz2, .xz),
    which triggers RepositoryDirectoryFileNotArchiveFileError.
    """
    validate_response(
        test_response=await admin_client.post(
            "/api/assets/upload",
            data={"is_directory": "true"},
            files={
                "file": ("testfile.txt", io.BytesIO(b"archive content"), "text/plain")
            },
        ),
        expected_json_schema=DIRECTORY_FILE_NOT_ARCHIVE_ERROR_JSON_SCHEMA,
        expected_status_code=415,
    )
