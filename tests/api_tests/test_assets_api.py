import io
import zipfile

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    ALL_ASSETS_JSON_SCHEMA,
    ASSET_JSON_SCHEMA,
    DIRECTORY_ARCHIVE_FORMAT_NOT_SPECIFIED_ERROR_JSON_SCHEMA,
    DIRECTORY_FILE_NOT_ARCHIVE_ERROR_JSON_SCHEMA,
    RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


def _build_zip_archive_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("inner.txt", "inner")
    return buffer.getvalue()


# Archive content for the directory uploads that have to actually unpack, as opposed to
# the ones below that are rejected on their filename before their content is read.
_ZIP_ARCHIVE_BYTES = _build_zip_archive_bytes()


async def test_get_all_assets(client):
    """All roles can GET /api/assets/all."""
    validate_response(
        test_response=await client.get("/api/assets/all"),
        expected_json_schema=ALL_ASSETS_JSON_SCHEMA,
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


async def test_upload_file_asset_stores_the_uploaded_filename_verbatim(admin_client):
    """POST /api/assets/upload records the uploaded filename as the asset's name."""
    response = await admin_client.post(
        "/api/assets/upload",
        data={"is_directory": "false"},
        files={"file": ("report.tar.gz", io.BytesIO(b"hello world"), "text/plain")},
    )
    body = response.json()
    # Nothing is split off the filename: the whole thing, multi-part suffix included, is
    # the name the asset is served under.
    assert body["name"] == "report.tar.gz"

    await admin_client.delete(f"/api/assets/{body['resource_id']}")


async def test_download_file_asset_is_served_under_its_name(admin_client):
    """GET /api/assets/download/{id} names the download after the asset's name."""
    upload_response = await admin_client.post(
        "/api/assets/upload",
        data={"is_directory": "false"},
        files={"file": ("report.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    asset_id = upload_response.json()["resource_id"]

    response = await admin_client.get(f"/api/assets/download/{asset_id}")

    assert response.status_code == 200
    assert response.content == b"hello world"
    # The asset is stored on the server under its bare resource ID, so the download has
    # to carry the name for the file to arrive as what the operator uploaded.
    assert 'filename="report.txt"' in response.headers["content-disposition"]

    await admin_client.delete(f"/api/assets/{asset_id}")


async def test_download_directory_asset_is_served_as_a_named_archive(admin_client):
    """GET /api/assets/download/{id} names a directory download after its name."""
    upload_response = await admin_client.post(
        "/api/assets/upload",
        data={"is_directory": "true", "name": "collection.v2"},
        files={
            "file": (
                "collection.zip",
                io.BytesIO(_ZIP_ARCHIVE_BYTES),
                "application/zip",
            )
        },
    )
    asset_id = upload_response.json()["resource_id"]

    response = await admin_client.get(f"/api/assets/download/{asset_id}")

    assert response.status_code == 200
    # A period in a directory's name is not a suffix to be replaced: the archive's own
    # extension is appended to the whole name.
    assert 'filename="collection.v2.zip"' in response.headers["content-disposition"]

    await admin_client.delete(f"/api/assets/{asset_id}")


async def test_download_file_asset_sanitizes_a_name_carrying_path_separators(
    admin_client,
):
    """GET /api/assets/download/{id} serves a traversing name under its last component."""
    upload_response = await admin_client.post(
        "/api/assets/upload",
        data={"is_directory": "false", "name": "../../escaped.txt"},
        files={"file": ("report.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    asset_id = upload_response.json()["resource_id"]
    # The name is recorded exactly as the operator gave it: the sanitation belongs to
    # serving the file, not to storing the name.
    assert upload_response.json()["name"] == "../../escaped.txt"

    response = await admin_client.get(f"/api/assets/download/{asset_id}")

    assert response.status_code == 200
    assert 'filename="escaped.txt"' in response.headers["content-disposition"]

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


async def test_update_asset_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """PATCH /api/assets/{id} returns 403 for spectators, 404 for admin/operator."""
    fake_uuid = "00000000-0000-4000-8000-000000000023"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.patch(
                f"/api/assets/{fake_uuid}", json={"name": "new-name"}
            ),
            expected_json_schema=RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.patch(
                f"/api/assets/{fake_uuid}", json={"name": "new-name"}
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_update_asset_by_invalid_uuid_returns_422(admin_client):
    """PATCH /api/assets/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.patch(
            "/api/assets/not-a-uuid", json={"name": "new-name"}
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_update_asset_updates_name_and_description(admin_client):
    """PATCH /api/assets/{id} updates the asset's name and description."""
    upload_response = await admin_client.post(
        "/api/assets/upload",
        data={"is_directory": "false"},
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    asset_id = upload_response.json()["resource_id"]

    response = await admin_client.patch(
        f"/api/assets/{asset_id}",
        json={"name": "renamed.txt", "description": "an updated description"},
    )
    validate_response(
        test_response=response,
        expected_json_schema=ASSET_JSON_SCHEMA,
        expected_status_code=200,
    )
    body = response.json()
    assert body["name"] == "renamed.txt"
    assert body["description"] == "an updated description"

    await admin_client.delete(f"/api/assets/{asset_id}")


async def test_update_asset_partial_update_preserves_other_fields(admin_client):
    """PATCH /api/assets/{id} with only a description leaves the name untouched."""
    upload_response = await admin_client.post(
        "/api/assets/upload",
        data={"is_directory": "false"},
        files={"file": ("original.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    asset_id = upload_response.json()["resource_id"]

    response = await admin_client.patch(
        f"/api/assets/{asset_id}",
        json={"description": "only the description changed"},
    )
    validate_response(
        test_response=response,
        expected_json_schema=ASSET_JSON_SCHEMA,
        expected_status_code=200,
    )
    body = response.json()
    assert body["name"] == "original.txt"
    assert body["description"] == "only the description changed"

    await admin_client.delete(f"/api/assets/{asset_id}")


async def test_update_asset_does_not_update_data_over_endpoint(admin_client):
    """PATCH /api/assets/{id} ignores a `data` field: only name/description are mutable."""
    upload_response = await admin_client.post(
        "/api/assets/upload",
        data={"is_directory": "false"},
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    asset_id = upload_response.json()["resource_id"]
    original_user_account = upload_response.json()["data"]["user_account"]

    response = await admin_client.patch(
        f"/api/assets/{asset_id}",
        json={
            "name": "renamed.txt",
            "data": {"user_account": {"username": "hacker", "role": "ADMIN"}},
        },
    )
    validate_response(
        test_response=response,
        expected_json_schema=ASSET_JSON_SCHEMA,
        expected_status_code=200,
    )
    body = response.json()
    assert body["name"] == "renamed.txt"
    # The `data` field from the request body is ignored: the stored attribution is
    # unchanged from what was recorded at upload.
    assert body["data"]["user_account"] == original_user_account

    await admin_client.delete(f"/api/assets/{asset_id}")


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
