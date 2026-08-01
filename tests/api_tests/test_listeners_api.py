import uuid

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    AGENT_TYPE_JSON_SCHEMA,
    EVENT_LOG_JSON_SCHEMA,
)
from tests.api_tests.utils import (
    create_listener_from_template,
    get_all_listener_ids,
    validate_response,
)

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
                                "detail": {"type": ["object", "null"]},
                            },
                            "required": ["code", "message", "detail"],
                        },
                    ],
                },
            },
            "required": ["state", "error"],
        },
        "event_log": EVENT_LOG_JSON_SCHEMA,
        "datetime_created": {"type": "string"},
        # Live references to the agents currently connected to the listener. Unlike the
        # persistent reference artifacts record, these embed the full agent type.
        "connected_agents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "name": {"type": "string"},
                    "agent_type": AGENT_TYPE_JSON_SCHEMA,
                },
                "required": ["agent_id", "name", "agent_type"],
            },
        },
        "creating_listener_template": {"type": "object"},
    },
    "required": [
        "name",
        "endpoint",
        "listener_type",
        "listener_id",
        "parameters",
        "status",
        "event_log",
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
                "detail": {"type": ["object", "null"]},
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
                "detail": {"type": ["object", "null"]},
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
                "detail": {"type": ["object", "null"]},
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
                "detail": {"type": ["object", "null"]},
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
                "detail": {"type": ["object", "null"]},
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


# Regression tests for the listener update path. A listener's name and description are
# display metadata that are set explicitly and are never derived from, or kept in sync
# with, its parameters. Updating one parameter therefore has to leave the name, the
# description and every other parameter exactly as they were. The endpoint is the one
# attribute that is deliberately re-derived on every parameter update.
@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_update_listener_parameter_leaves_everything_else_alone(
    admin_client, mock_listener_template_ids
):
    for template_id in mock_listener_template_ids:
        create_response = await create_listener_from_template(
            admin_client=admin_client,
            listener_template_id=template_id,
            name="name-set-at-creation",
            description="description set at creation",
        )
        assert create_response.status_code == 201, create_response.text
        created_listener = create_response.json()
        listener_id = created_listener["listener_id"]
        original_parameters = created_listener["parameters"]

        # timeout is declared by both mock listener templates
        update_response = await admin_client.patch(
            f"/api/listeners/{listener_id}",
            json={"parameters": {"timeout": 99}},
        )
        assert update_response.status_code == 200, update_response.text
        updated_listener = update_response.json()

        assert updated_listener["name"] == "name-set-at-creation", (
            "Updating a parameter must not change the listener's name"
        )
        assert updated_listener["description"] == "description set at creation", (
            "Updating a parameter must not change the listener's description"
        )
        assert updated_listener["parameters"]["timeout"] == 99
        untouched_parameters = {
            parameter_name: value
            for parameter_name, value in updated_listener["parameters"].items()
            if parameter_name != "timeout"
        }
        assert untouched_parameters == {
            parameter_name: value
            for parameter_name, value in original_parameters.items()
            if parameter_name != "timeout"
        }, "Updating one parameter must not change any of the others"

        # A GET has to agree with what the PATCH returned
        get_response = await admin_client.get(f"/api/listeners/{listener_id}")
        assert get_response.json()["name"] == "name-set-at-creation"
        assert get_response.json()["description"] == "description set at creation"
        assert get_response.json()["parameters"] == updated_listener["parameters"]


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_update_listener_name_option_does_not_rename_the_listener(
    admin_client, mock_listener_template_ids
):
    """Updating a parameter that happens to be called "name" is just a parameter update.

    Both mock listener templates declare an option called "name". Updating it must move
    the parameter and nothing else: the listener's own name is unrelated to it.
    """
    for template_id in mock_listener_template_ids:
        create_response = await create_listener_from_template(
            admin_client=admin_client,
            listener_template_id=template_id,
            option_overrides={"name": "original-option-value"},
            name="the-listeners-actual-name",
        )
        assert create_response.status_code == 201, create_response.text
        listener_id = create_response.json()["listener_id"]

        update_response = await admin_client.patch(
            f"/api/listeners/{listener_id}",
            json={"parameters": {"name": "updated-option-value"}},
        )
        assert update_response.status_code == 200, update_response.text
        updated_listener = update_response.json()

        assert updated_listener["parameters"]["name"] == "updated-option-value"
        assert updated_listener["name"] == "the-listeners-actual-name", (
            "Updating a parameter called 'name' must not rename the listener"
        )


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_rename_listener_then_update_parameter_keeps_the_new_name(
    admin_client, mock_listener_template_ids
):
    """An explicit rename survives a later parameter update.

    This is the original defect: the update path rebuilt the listener's name from the
    creating template, silently discarding whatever the listener had been renamed to.
    """
    for template_id in mock_listener_template_ids:
        create_response = await create_listener_from_template(
            admin_client=admin_client,
            listener_template_id=template_id,
        )
        assert create_response.status_code == 201, create_response.text
        listener_id = create_response.json()["listener_id"]

        rename_response = await admin_client.patch(
            f"/api/listeners/{listener_id}",
            json={"name": "renamed-after-creation"},
        )
        assert rename_response.status_code == 200, rename_response.text
        assert rename_response.json()["name"] == "renamed-after-creation"

        update_response = await admin_client.patch(
            f"/api/listeners/{listener_id}",
            json={"parameters": {"timeout": 45}},
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["name"] == "renamed-after-creation", (
            "A parameter update must not revert an explicit rename"
        )

        # And it stays renamed across any number of further parameter updates
        for timeout in (46, 47, 48):
            update_response = await admin_client.patch(
                f"/api/listeners/{listener_id}",
                json={"parameters": {"timeout": timeout}},
            )
            assert update_response.json()["name"] == "renamed-after-creation"


@pytest.mark.usefixtures("delete_listeners_after_test")
async def test_update_listener_parameter_still_rederives_the_endpoint(
    admin_client, mock_listener_template_ids
):
    """The endpoint is still derived from the parameters even though the name is not.

    The mock_1 listener template derives its endpoint from the timeout parameter, so
    updating that parameter has to move the endpoint with it. The mock_2 template
    ignores its parameters entirely, so its endpoint stays put.
    """
    for template_id in mock_listener_template_ids:
        template = (
            await admin_client.get(f"/api/listener-templates/{template_id}")
        ).json()
        # Only the mock_1 template builds its endpoint out of a parameter
        endpoint_is_derived_from_parameters = (
            template["label"] == "consortium.listeners.mock_1"
        )

        create_response = await create_listener_from_template(
            admin_client=admin_client,
            listener_template_id=template_id,
            name="endpoint-derivation-listener",
        )
        assert create_response.status_code == 201, create_response.text
        created_listener = create_response.json()
        listener_id = created_listener["listener_id"]
        original_endpoint = created_listener["endpoint"]

        update_response = await admin_client.patch(
            f"/api/listeners/{listener_id}",
            json={"parameters": {"timeout": 77}},
        )
        assert update_response.status_code == 200, update_response.text
        updated_listener = update_response.json()

        if endpoint_is_derived_from_parameters:
            assert updated_listener["endpoint"] != original_endpoint, (
                "An endpoint derived from a parameter must be re-derived when that "
                "parameter is updated"
            )
            assert "77" in updated_listener["endpoint"]
        else:
            assert updated_listener["endpoint"] == original_endpoint

        assert updated_listener["name"] == "endpoint-derivation-listener", (
            "Re-deriving the endpoint must not drag the name along with it"
        )


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
