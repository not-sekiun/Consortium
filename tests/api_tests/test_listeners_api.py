import uuid

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import get_all_listener_ids, validate_response

pytestmark = pytest.mark.anyio

LISTENER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "endpoint": {"type": "string"},
        "listener_type": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "registered_compatible_agent_types": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["name", "registered_compatible_agent_types"],
        },
        "listener_id": {"type": "string"},
        "parameters": {"type": "object"},
        "status": {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "error": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "message": {"type": "string"},
                                "detail": {},
                            },
                            "required": ["code", "message", "detail"],
                        },
                    ],
                },
            },
            "required": ["state", "error"],
        },
        "datetime_created": {"type": "string"},
        "connected_agents": {"type": "array"},
        "creating_listener_template": {"type": "object"},
    },
    "required": [
        "name",
        "endpoint",
        "listener_type",
        "listener_id",
        "parameters",
        "status",
    ],
}
ALL_LISTENERS_JSON_SCHEMA = {
    "type": "array",
    "items": LISTENER_JSON_SCHEMA,
}
LISTENER_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["LISTENER_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
LISTENER_ALREADY_RUNNING_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["LISTENER_ALREADY_RUNNING_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
LISTENER_NOT_RUNNING_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["LISTENER_NOT_RUNNING_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
INVALID_LISTENER_PARAMETER_NAME_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["INVALID_LISTENER_PARAMETER_NAME_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
INVALID_LISTENER_PARAMETER_VALUE_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["INVALID_LISTENER_PARAMETER_VALUE_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_get_all_listeners(client):
    validate_response(
        test_response=await client.get("/api/listeners/all"),
        expected_json_schema=ALL_LISTENERS_JSON_SCHEMA,
        expected_status_code=200,
    )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_get_listener_by_listener_id(admin_client, client):
    for listener_id in await get_all_listener_ids(admin_client):
        validate_response(
            test_response=await client.get(f"/api/listeners/{listener_id}"),
            expected_json_schema=LISTENER_JSON_SCHEMA,
            expected_status_code=200,
        )


async def test_get_listener_by_invalid_listener_id_returns_404(admin_client):
    """A valid UUID4 that does not correspond to a listener returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000000"
    validate_response(
        test_response=await admin_client.get(f"/api/listeners/{fake_uuid}"),
        expected_json_schema=LISTENER_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_get_listener_by_invalid_uuid_returns_422(admin_client):
    """GET /api/listeners/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/listeners/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_start_listener_by_listener_id(admin_client, spectator_client, client):
    if client != spectator_client:
        for listener_id in await get_all_listener_ids(admin_client):
            validate_response(
                test_response=await client.post(f"/api/listeners/{listener_id}/start"),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=202,
            )
            validate_response(
                test_response=await admin_client.post(
                    f"/api/listeners/{listener_id}/stop"
                ),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=202,
            )
    else:
        for listener_id in await get_all_listener_ids(admin_client):
            validate_response(
                test_response=await spectator_client.post(
                    f"/api/listeners/{listener_id}/start"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_start_listener_already_running_returns_409(admin_client):
    """Starting an already-running listener returns 409."""
    for listener_id in await get_all_listener_ids(admin_client):
        await admin_client.post(f"/api/listeners/{listener_id}/start")
        validate_response(
            test_response=await admin_client.post(
                f"/api/listeners/{listener_id}/start"
            ),
            expected_json_schema=LISTENER_ALREADY_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )
        await admin_client.post(f"/api/listeners/{listener_id}/stop")


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_stop_listener_by_listener_id(admin_client, spectator_client, client):
    if client != spectator_client:
        for listener_id in await get_all_listener_ids(admin_client):
            await admin_client.post(f"/api/listeners/{listener_id}/start")
            validate_response(
                test_response=await client.post(f"/api/listeners/{listener_id}/stop"),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=202,
            )
    else:
        for listener_id in await get_all_listener_ids(admin_client):
            await admin_client.post(f"/api/listeners/{listener_id}/start")
            validate_response(
                test_response=await spectator_client.post(
                    f"/api/listeners/{listener_id}/stop"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.post(f"/api/listeners/{listener_id}/stop")


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_stop_listener_not_running_returns_409(admin_client):
    """Stopping a listener that is not running returns 409."""
    for listener_id in await get_all_listener_ids(admin_client):
        validate_response(
            test_response=await admin_client.post(f"/api/listeners/{listener_id}/stop"),
            expected_json_schema=LISTENER_NOT_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_cancel_listener_by_listener_id(admin_client, spectator_client, client):
    if client != spectator_client:
        for listener_id in await get_all_listener_ids(admin_client):
            await admin_client.post(f"/api/listeners/{listener_id}/start")
            validate_response(
                test_response=await client.post(f"/api/listeners/{listener_id}/cancel"),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=202,
            )
    else:
        for listener_id in await get_all_listener_ids(admin_client):
            await admin_client.post(f"/api/listeners/{listener_id}/start")
            validate_response(
                test_response=await spectator_client.post(
                    f"/api/listeners/{listener_id}/cancel"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.post(f"/api/listeners/{listener_id}/cancel")


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_update_listener_by_listener_id(admin_client, spectator_client, client):
    new_name = uuid.uuid4().hex
    new_description = uuid.uuid4().hex

    if client != spectator_client:
        for listener_id in await get_all_listener_ids(admin_client):
            # The endpoint is PATCH, not PUT
            validate_response(
                test_response=await client.patch(
                    f"/api/listeners/{listener_id}",
                    json={"name": new_name, "description": new_description},
                ),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=200,
            )
            validate_response(
                test_response=await client.get(f"/api/listeners/{listener_id}"),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=200,
                validator_function=lambda r: (
                    r.json()["name"] == new_name
                    and r.json()["description"] == new_description
                ),
            )
    else:
        for listener_id in await get_all_listener_ids(admin_client):
            validate_response(
                test_response=await spectator_client.patch(
                    f"/api/listeners/{listener_id}",
                    json={"name": new_name},
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_update_running_listener_returns_409(admin_client):
    """PATCH parameters on a running listener returns 409; name/description updates are always allowed."""
    for listener_id in await get_all_listener_ids(admin_client):
        await admin_client.post(f"/api/listeners/{listener_id}/start")
        # Updating parameters while running is blocked
        response = await admin_client.patch(
            f"/api/listeners/{listener_id}",
            json={"parameters": {}},
        )
        assert response.status_code == 409, (
            f"Expected 409 when patching parameters on running listener, got {response.status_code}"
        )
        # Updating only name/description is always safe regardless of state
        name_response = await admin_client.patch(
            f"/api/listeners/{listener_id}",
            json={"name": "new-name"},
        )
        assert name_response.status_code == 200, (
            f"Expected 200 when patching name on running listener, got {name_response.status_code}"
        )
        desc_response = await admin_client.patch(
            f"/api/listeners/{listener_id}",
            json={"description": "new-description"},
        )
        assert desc_response.status_code == 200, (
            f"Expected 200 when patching description on running listener, got {desc_response.status_code}"
        )
        await admin_client.post(f"/api/listeners/{listener_id}/stop")


@pytest.mark.usefixtures("create_listeners_before_test")
async def test_delete_listener_by_listener_id(admin_client, spectator_client, client):
    if client != spectator_client:
        for listener_id in await get_all_listener_ids(admin_client):
            validate_response(
                test_response=await client.delete(f"/api/listeners/{listener_id}"),
                expected_status_code=204,
            )
    else:
        for listener_id in await get_all_listener_ids(admin_client):
            validate_response(
                test_response=await spectator_client.delete(
                    f"/api/listeners/{listener_id}"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.delete(f"/api/listeners/{listener_id}")


async def test_start_listener_not_found_returns_404(admin_client):
    """POST /{id}/start with a valid UUID4 that has no matching listener returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000030"
    validate_response(
        test_response=await admin_client.post(f"/api/listeners/{fake_uuid}/start"),
        expected_json_schema=LISTENER_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_start_listener_by_invalid_uuid_returns_422(admin_client):
    """POST /{id}/start with a non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.post("/api/listeners/not-a-uuid/start"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_stop_listener_not_found_returns_404(admin_client):
    """POST /{id}/stop with a valid UUID4 that has no matching listener returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000031"
    validate_response(
        test_response=await admin_client.post(f"/api/listeners/{fake_uuid}/stop"),
        expected_json_schema=LISTENER_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_stop_listener_by_invalid_uuid_returns_422(admin_client):
    """POST /{id}/stop with a non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.post("/api/listeners/not-a-uuid/stop"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_cancel_listener_not_found_returns_404(admin_client):
    """POST /{id}/cancel with a valid UUID4 that has no matching listener returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000032"
    validate_response(
        test_response=await admin_client.post(f"/api/listeners/{fake_uuid}/cancel"),
        expected_json_schema=LISTENER_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_cancel_listener_not_running_returns_409(admin_client):
    """POST /{id}/cancel on a listener that is not running returns 409."""
    for listener_id in await get_all_listener_ids(admin_client):
        validate_response(
            test_response=await admin_client.post(
                f"/api/listeners/{listener_id}/cancel"
            ),
            expected_json_schema=LISTENER_NOT_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )


async def test_cancel_listener_by_invalid_uuid_returns_422(admin_client):
    """POST /{id}/cancel with a non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.post("/api/listeners/not-a-uuid/cancel"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_update_listener_not_found_returns_404(admin_client):
    """PATCH /{id} with a valid UUID4 that has no matching listener returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000033"
    validate_response(
        test_response=await admin_client.patch(
            f"/api/listeners/{fake_uuid}",
            json={"name": "new-name"},
        ),
        expected_json_schema=LISTENER_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_update_listener_with_invalid_parameter_name_returns_422(admin_client):
    """PATCH /{id} with an unrecognised parameter name returns 422."""
    for listener_id in await get_all_listener_ids(admin_client):
        validate_response(
            test_response=await admin_client.patch(
                f"/api/listeners/{listener_id}",
                json={"parameters": {"nonexistent_parameter": "value"}},
            ),
            expected_json_schema=INVALID_LISTENER_PARAMETER_NAME_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_update_listener_with_invalid_parameter_value_returns_422(admin_client):
    """PATCH /{id} with a wrong-type value for a known parameter returns 422."""
    for listener_id in await get_all_listener_ids(admin_client):
        validate_response(
            test_response=await admin_client.patch(
                f"/api/listeners/{listener_id}",
                # timeout is an int; passing a string triggers the value error
                json={"parameters": {"timeout": "not_an_int"}},
            ),
            expected_json_schema=INVALID_LISTENER_PARAMETER_VALUE_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_delete_running_listener_returns_409(admin_client):
    """DELETE /{id} on a running listener returns 409."""
    for listener_id in await get_all_listener_ids(admin_client):
        await admin_client.post(f"/api/listeners/{listener_id}/start")
        validate_response(
            test_response=await admin_client.delete(f"/api/listeners/{listener_id}"),
            expected_json_schema=LISTENER_ALREADY_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )
        await admin_client.post(f"/api/listeners/{listener_id}/stop")


async def test_delete_listener_not_found_returns_404(admin_client):
    """DELETE /{id} with a valid UUID4 that has no matching listener returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000034"
    validate_response(
        test_response=await admin_client.delete(f"/api/listeners/{fake_uuid}"),
        expected_json_schema=LISTENER_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_listener_by_invalid_uuid_returns_422(admin_client):
    """DELETE /{id} with a non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.delete("/api/listeners/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )
