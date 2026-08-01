import uuid

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    AGENT_GENERATOR_JSON_SCHEMA,
)
from tests.api_tests.utils import (
    build_create_request_body,
    create_agent_generator_from_template,
    validate_response,
)

pytestmark = pytest.mark.anyio

ALL_AGENT_GENERATORS_JSON_SCHEMA = {
    "type": "array",
    "items": AGENT_GENERATOR_JSON_SCHEMA,
}
AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_GENERATOR_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {"type": ["object", "null"]},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
AGENT_GENERATOR_ALREADY_RUNNING_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_GENERATOR_ALREADY_RUNNING_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {"type": ["object", "null"]},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
AGENT_GENERATOR_NOT_RUNNING_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_GENERATOR_NOT_RUNNING_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {"type": ["object", "null"]},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
INVALID_AGENT_GENERATOR_PARAMETER_NAME_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["INVALID_AGENT_GENERATOR_PARAMETER_NAME_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {"type": ["object", "null"]},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
INVALID_AGENT_GENERATOR_PARAMETER_VALUE_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["INVALID_AGENT_GENERATOR_PARAMETER_VALUE_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {"type": ["object", "null"]},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


async def _create_one_agent_generator_per_template(
    admin_client,
    template_ids: list[str],
) -> list[str]:
    agent_generator_ids = []
    for template_id in template_ids:
        template = (
            await admin_client.get(f"/api/agent-templates/{template_id}")
        ).json()
        options_payload = {
            name: opt["default_value"] for name, opt in template["options"].items()
        }
        response = await admin_client.post(
            f"/api/agent-templates/{template_id}",
            json=build_create_request_body(options=options_payload),
        )
        if response.status_code == 201:
            agent_generator_ids.append(response.json()["agent_generator_id"])
    return agent_generator_ids


async def test_get_all_agent_generators_empty(client):
    """GET /api/agent-generators/all returns an empty list when none exist."""
    validate_response(
        test_response=await client.get("/api/agent-generators/all"),
        expected_json_schema=ALL_AGENT_GENERATORS_JSON_SCHEMA,
        expected_status_code=200,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_get_all_agent_generators(admin_client, client, mock_agent_template_ids):
    await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    validate_response(
        test_response=await client.get("/api/agent-generators/all"),
        expected_json_schema=ALL_AGENT_GENERATORS_JSON_SCHEMA,
        expected_status_code=200,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_get_agent_generator_by_agent_generator_id(
    admin_client, client, mock_agent_template_ids
):
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        validate_response(
            test_response=await client.get(f"/api/agent-generators/{ag_id}"),
            expected_json_schema=AGENT_GENERATOR_JSON_SCHEMA,
            expected_status_code=200,
        )


async def test_get_agent_generator_by_invalid_id_returns_404(admin_client):
    """A valid UUID4 that does not match any agent generator returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000002"
    validate_response(
        test_response=await admin_client.get(f"/api/agent-generators/{fake_uuid}"),
        expected_json_schema=AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_start_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client, mock_agent_template_ids
):
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        if client != spectator_client:
            validate_response(
                test_response=await client.post(f"/api/agent-generators/{ag_id}/start"),
                expected_status_code=202,
            )
            await admin_client.post(f"/api/agent-generators/{ag_id}/stop")
        else:
            validate_response(
                test_response=await client.post(f"/api/agent-generators/{ag_id}/start"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_start_agent_generator_already_running_returns_409(
    admin_client, mock_agent_template_ids
):
    """Starting an already-running agent generator returns 409."""
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        await admin_client.post(f"/api/agent-generators/{ag_id}/start")
        validate_response(
            test_response=await admin_client.post(
                f"/api/agent-generators/{ag_id}/start"
            ),
            expected_json_schema=AGENT_GENERATOR_ALREADY_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )
        await admin_client.post(f"/api/agent-generators/{ag_id}/stop")


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_stop_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client, mock_agent_template_ids
):
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        if client != spectator_client:
            await admin_client.post(f"/api/agent-generators/{ag_id}/start")
            validate_response(
                test_response=await client.post(f"/api/agent-generators/{ag_id}/stop"),
                expected_status_code=202,
            )
        else:
            await admin_client.post(f"/api/agent-generators/{ag_id}/start")
            validate_response(
                test_response=await client.post(f"/api/agent-generators/{ag_id}/stop"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.post(f"/api/agent-generators/{ag_id}/stop")


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_stop_agent_generator_not_running_returns_409(
    admin_client, mock_agent_template_ids
):
    """Stopping an agent generator that is not running returns 409."""
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        validate_response(
            test_response=await admin_client.post(
                f"/api/agent-generators/{ag_id}/stop"
            ),
            expected_json_schema=AGENT_GENERATOR_NOT_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_cancel_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client, mock_agent_template_ids
):
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        if client != spectator_client:
            await admin_client.post(f"/api/agent-generators/{ag_id}/start")
            validate_response(
                test_response=await client.post(
                    f"/api/agent-generators/{ag_id}/cancel"
                ),
                expected_status_code=202,
            )
        else:
            await admin_client.post(f"/api/agent-generators/{ag_id}/start")
            validate_response(
                test_response=await client.post(
                    f"/api/agent-generators/{ag_id}/cancel"
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.post(f"/api/agent-generators/{ag_id}/cancel")


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_update_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client, mock_agent_template_ids
):
    new_name = uuid.uuid4().hex
    new_description = uuid.uuid4().hex
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        if client != spectator_client:
            validate_response(
                test_response=await client.patch(
                    f"/api/agent-generators/{ag_id}",
                    json={"name": new_name, "description": new_description},
                ),
                expected_json_schema=AGENT_GENERATOR_JSON_SCHEMA,
                expected_status_code=200,
                validator_function=lambda r, n=new_name, d=new_description: (
                    r.json()["name"] == n and r.json()["description"] == d
                ),
            )
        else:
            validate_response(
                test_response=await client.patch(
                    f"/api/agent-generators/{ag_id}",
                    json={"name": new_name},
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_update_running_agent_generator_returns_409(
    admin_client, mock_agent_template_ids
):
    """PATCH parameters on a running agent generator returns 409; name/description updates are always allowed."""
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        await admin_client.post(f"/api/agent-generators/{ag_id}/start")
        # Updating parameters while running is blocked
        response = await admin_client.patch(
            f"/api/agent-generators/{ag_id}",
            json={"parameters": {}},
        )
        assert response.status_code == 409, (
            f"Expected 409 when patching parameters on running agent generator, got {response.status_code}"
        )
        # Updating only name/description is always safe regardless of state
        name_response = await admin_client.patch(
            f"/api/agent-generators/{ag_id}",
            json={"name": "new-name"},
        )
        assert name_response.status_code == 200, (
            f"Expected 200 when patching name on running agent generator, got {name_response.status_code}"
        )
        desc_response = await admin_client.patch(
            f"/api/agent-generators/{ag_id}",
            json={"description": "new-description"},
        )
        assert desc_response.status_code == 200, (
            f"Expected 200 when patching description on running agent generator, got {desc_response.status_code}"
        )
        await admin_client.post(f"/api/agent-generators/{ag_id}/stop")


# Regression tests for the agent generator update path. An agent generator's name and
# description are display metadata that are set explicitly and are never derived from, or
# kept in sync with, its parameters. Updating one parameter therefore has to leave the
# name, the description and every other parameter exactly as they were.
@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_update_agent_generator_parameter_leaves_everything_else_alone(
    admin_client, mock_agent_template_ids
):
    for template_id in mock_agent_template_ids:
        create_response = await create_agent_generator_from_template(
            admin_client=admin_client,
            agent_template_id=template_id,
            name="name-set-at-creation",
            description="description set at creation",
        )
        assert create_response.status_code == 201, create_response.text
        created_agent_generator = create_response.json()
        ag_id = created_agent_generator["agent_generator_id"]
        original_parameters = created_agent_generator["parameters"]

        # retry_count is declared by both mock agent templates
        update_response = await admin_client.patch(
            f"/api/agent-generators/{ag_id}",
            json={"parameters": {"retry_count": 9}},
        )
        assert update_response.status_code == 200, update_response.text
        updated_agent_generator = update_response.json()

        assert updated_agent_generator["name"] == "name-set-at-creation", (
            "Updating a parameter must not change the agent generator's name"
        )
        assert (
            updated_agent_generator["description"] == "description set at creation"
        ), "Updating a parameter must not change the agent generator's description"
        assert updated_agent_generator["parameters"]["retry_count"] == 9
        untouched_parameters = {
            parameter_name: value
            for parameter_name, value in updated_agent_generator["parameters"].items()
            if parameter_name != "retry_count"
        }
        assert untouched_parameters == {
            parameter_name: value
            for parameter_name, value in original_parameters.items()
            if parameter_name != "retry_count"
        }, "Updating one parameter must not change any of the others"

        # A GET has to agree with what the PATCH returned
        get_response = await admin_client.get(f"/api/agent-generators/{ag_id}")
        assert get_response.json()["name"] == "name-set-at-creation"
        assert get_response.json()["description"] == "description set at creation"
        assert (
            get_response.json()["parameters"] == updated_agent_generator["parameters"]
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_update_agent_generator_name_option_does_not_rename_the_generator(
    admin_client, mock_agent_template_ids
):
    """Updating a parameter that happens to be called "name" is just a parameter update.

    Both mock agent templates declare an option called "name". Updating it must move the
    parameter and nothing else: the agent generator's own name is unrelated to it.
    """
    for template_id in mock_agent_template_ids:
        create_response = await create_agent_generator_from_template(
            admin_client=admin_client,
            agent_template_id=template_id,
            option_overrides={"name": "original-option-value"},
            name="the-generators-actual-name",
        )
        assert create_response.status_code == 201, create_response.text
        ag_id = create_response.json()["agent_generator_id"]

        update_response = await admin_client.patch(
            f"/api/agent-generators/{ag_id}",
            json={"parameters": {"name": "updated-option-value"}},
        )
        assert update_response.status_code == 200, update_response.text
        updated_agent_generator = update_response.json()

        assert updated_agent_generator["parameters"]["name"] == "updated-option-value"
        assert updated_agent_generator["name"] == "the-generators-actual-name", (
            "Updating a parameter called 'name' must not rename the agent generator"
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_rename_agent_generator_then_update_parameter_keeps_the_new_name(
    admin_client, mock_agent_template_ids
):
    """An explicit rename survives a later parameter update.

    This is the original defect: the update path rebuilt the agent generator's name from
    the creating template, silently discarding whatever it had been renamed to.
    """
    for template_id in mock_agent_template_ids:
        create_response = await create_agent_generator_from_template(
            admin_client=admin_client,
            agent_template_id=template_id,
        )
        assert create_response.status_code == 201, create_response.text
        ag_id = create_response.json()["agent_generator_id"]

        rename_response = await admin_client.patch(
            f"/api/agent-generators/{ag_id}",
            json={"name": "renamed-after-creation"},
        )
        assert rename_response.status_code == 200, rename_response.text
        assert rename_response.json()["name"] == "renamed-after-creation"

        update_response = await admin_client.patch(
            f"/api/agent-generators/{ag_id}",
            json={"parameters": {"retry_count": 4}},
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["name"] == "renamed-after-creation", (
            "A parameter update must not revert an explicit rename"
        )

        # And it stays renamed across any number of further parameter updates
        for retry_count in (5, 6, 7):
            update_response = await admin_client.patch(
                f"/api/agent-generators/{ag_id}",
                json={"parameters": {"retry_count": retry_count}},
            )
            assert update_response.json()["name"] == "renamed-after-creation"


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_delete_agent_generator_by_agent_generator_id(
    admin_client, spectator_client, client, mock_agent_template_ids
):
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        if client != spectator_client:
            validate_response(
                test_response=await client.delete(f"/api/agent-generators/{ag_id}"),
                expected_status_code=204,
            )
        else:
            validate_response(
                test_response=await client.delete(f"/api/agent-generators/{ag_id}"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            await admin_client.delete(f"/api/agent-generators/{ag_id}")


async def test_delete_agent_generator_not_found(admin_client):
    """Deleting a non-existent agent generator returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000003"
    validate_response(
        test_response=await admin_client.delete(f"/api/agent-generators/{fake_uuid}"),
        expected_json_schema=AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_get_agent_generator_by_invalid_uuid_returns_422(admin_client):
    """GET /api/agent-generators/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/agent-generators/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_delete_agent_generator_by_invalid_uuid_returns_422(admin_client):
    """DELETE /api/agent-generators/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.delete("/api/agent-generators/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_start_agent_generator_not_found_returns_404(admin_client):
    """POST /{id}/start with a valid UUID4 that has no matching generator returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000040"
    validate_response(
        test_response=await admin_client.post(
            f"/api/agent-generators/{fake_uuid}/start"
        ),
        expected_json_schema=AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_start_agent_generator_by_invalid_uuid_returns_422(admin_client):
    """POST /{id}/start with a non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.post("/api/agent-generators/not-a-uuid/start"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_stop_agent_generator_not_found_returns_404(admin_client):
    """POST /{id}/stop with a valid UUID4 that has no matching generator returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000041"
    validate_response(
        test_response=await admin_client.post(
            f"/api/agent-generators/{fake_uuid}/stop"
        ),
        expected_json_schema=AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_stop_agent_generator_by_invalid_uuid_returns_422(admin_client):
    """POST /{id}/stop with a non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.post("/api/agent-generators/not-a-uuid/stop"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_cancel_agent_generator_not_found_returns_404(admin_client):
    """POST /{id}/cancel with a valid UUID4 that has no matching generator returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000042"
    validate_response(
        test_response=await admin_client.post(
            f"/api/agent-generators/{fake_uuid}/cancel"
        ),
        expected_json_schema=AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_cancel_agent_generator_not_running_returns_409(
    admin_client, mock_agent_template_ids
):
    """POST /{id}/cancel on a generator that is not running returns 409."""
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        validate_response(
            test_response=await admin_client.post(
                f"/api/agent-generators/{ag_id}/cancel"
            ),
            expected_json_schema=AGENT_GENERATOR_NOT_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )


async def test_cancel_agent_generator_by_invalid_uuid_returns_422(admin_client):
    """POST /{id}/cancel with a non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.post(
            "/api/agent-generators/not-a-uuid/cancel"
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_update_agent_generator_not_found_returns_404(admin_client):
    """PATCH /{id} with a valid UUID4 that has no matching generator returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000043"
    validate_response(
        test_response=await admin_client.patch(
            f"/api/agent-generators/{fake_uuid}",
            json={"name": "new-name"},
        ),
        expected_json_schema=AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_update_agent_generator_by_invalid_uuid_returns_422(admin_client):
    """PATCH /{id} with a non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.patch(
            "/api/agent-generators/not-a-uuid",
            json={"name": "new-name"},
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_update_agent_generator_with_invalid_parameter_name_returns_422(
    admin_client, mock_agent_template_ids
):
    """PATCH /{id} with an unrecognised parameter name returns 422."""
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        validate_response(
            test_response=await admin_client.patch(
                f"/api/agent-generators/{ag_id}",
                json={"parameters": {"nonexistent_parameter": "value"}},
            ),
            expected_json_schema=INVALID_AGENT_GENERATOR_PARAMETER_NAME_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_update_agent_generator_with_invalid_parameter_value_returns_422(
    admin_client, mock_agent_template_ids
):
    """PATCH /{id} with a wrong-type value for a known parameter returns 422."""
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        validate_response(
            test_response=await admin_client.patch(
                f"/api/agent-generators/{ag_id}",
                # retry_count is an int; passing a string triggers the value error
                json={"parameters": {"retry_count": "not_an_int"}},
            ),
            expected_json_schema=INVALID_AGENT_GENERATOR_PARAMETER_VALUE_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
async def test_delete_running_agent_generator_returns_409(
    admin_client, mock_agent_template_ids
):
    """DELETE /{id} on a running agent generator returns 409."""
    ag_ids = await _create_one_agent_generator_per_template(
        admin_client, mock_agent_template_ids
    )
    for ag_id in ag_ids:
        await admin_client.post(f"/api/agent-generators/{ag_id}/start")
        validate_response(
            test_response=await admin_client.delete(f"/api/agent-generators/{ag_id}"),
            expected_json_schema=AGENT_GENERATOR_ALREADY_RUNNING_ERROR_JSON_SCHEMA,
            expected_status_code=409,
        )
        await admin_client.post(f"/api/agent-generators/{ag_id}/stop")
