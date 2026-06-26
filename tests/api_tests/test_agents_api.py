import asyncio

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

AGENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "endpoint": {"type": "string"},
        "agent_type": {"type": "object"},
        "status": {"type": "string"},
    },
    "required": ["agent_id", "name", "description", "endpoint", "agent_type", "status"],
}
ALL_AGENTS_JSON_SCHEMA = {
    "type": "array",
    "items": AGENT_JSON_SCHEMA,
}
AGENT_TASK_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "command": {"type": "string"},
        "arguments": {"type": "object"},
        "status": {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
            },
            "required": ["state"],
        },
        "events": {
            "type": "object",
            "properties": {
                "total_count": {"type": "integer"},
                "entries": {"type": "array"},
            },
            "required": ["total_count", "entries"],
        },
        "datetime_created": {"type": "string"},
    },
    "required": [
        "task_id",
        "command",
        "arguments",
        "status",
        "events",
        "datetime_created",
    ],
}
ALL_AGENT_TASKS_JSON_SCHEMA = {
    "type": "array",
    "items": AGENT_TASK_JSON_SCHEMA,
}
AGENT_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["AGENT_NOT_FOUND_ERROR"]},
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
AGENT_TASK_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["AGENT_TASK_NOT_FOUND_ERROR"]},
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
AGENT_CAPABILITY_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_CAPABILITY_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


# ---------------------------------------------------------------------------
# Tests that require no connected agents
# ---------------------------------------------------------------------------


async def test_get_all_agents_returns_empty_list(client):
    """GET /api/agents/all returns empty list when no agents are connected."""
    validate_response(
        test_response=await client.get("/api/agents/all"),
        expected_json_schema=ALL_AGENTS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json() == [],
    )


async def test_get_agent_by_invalid_id_returns_404(client):
    """GET /api/agents/{id} with unknown valid UUID4 returns 404 for all roles."""
    fake_uuid = "00000000-0000-4000-8000-000000000010"
    validate_response(
        test_response=await client.get(f"/api/agents/{fake_uuid}"),
        expected_json_schema=AGENT_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_get_all_agent_tasks_returns_empty_list(client):
    """GET /api/agents/tasks returns empty list when no tasks exist."""
    validate_response(
        test_response=await client.get("/api/agents/tasks"),
        expected_json_schema=ALL_AGENT_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json() == [],
    )


async def test_get_agent_task_by_invalid_id_returns_404(client):
    """GET /api/agents/tasks/{task_id} with unknown valid UUID4 returns 404 for all roles."""
    fake_uuid = "00000000-0000-4000-8000-000000000011"
    validate_response(
        test_response=await client.get(f"/api/agents/tasks/{fake_uuid}"),
        expected_json_schema=AGENT_TASK_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_get_all_agent_tasks_by_agent_id_returns_404(client):
    """GET /api/agents/{agent_id}/tasks with unknown agent returns 404 for all roles."""
    fake_uuid = "00000000-0000-4000-8000-000000000012"
    validate_response(
        test_response=await client.get(f"/api/agents/{fake_uuid}/tasks"),
        expected_json_schema=AGENT_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_update_agent_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """PATCH /api/agents/{id} returns 403 for spectators, 404 for admin/operator."""
    fake_uuid = "00000000-0000-4000-8000-000000000013"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.patch(
                f"/api/agents/{fake_uuid}",
                json={"name": "new-name"},
            ),
            expected_json_schema=AGENT_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.patch(
                f"/api/agents/{fake_uuid}",
                json={"name": "new-name"},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_task_agent_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """POST /api/agents/{id}/tasks returns 403 for spectators, 404 for admin/operator."""
    fake_uuid = "00000000-0000-4000-8000-000000000014"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.post(
                f"/api/agents/{fake_uuid}/tasks",
                json={"command": "shell", "arguments": {}},
            ),
            expected_json_schema=AGENT_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.post(
                f"/api/agents/{fake_uuid}/tasks",
                json={"command": "shell", "arguments": {}},
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_get_agent_by_invalid_uuid_returns_422(admin_client):
    """GET /api/agents/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/agents/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_get_agent_task_by_invalid_uuid_returns_422(admin_client):
    """GET /api/agents/tasks/{task_id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/agents/tasks/not-a-uuid"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_get_agent_tasks_by_invalid_agent_uuid_returns_422(admin_client):
    """GET /api/agents/{agent_id}/tasks with non-UUID4 agent_id returns 422."""
    validate_response(
        test_response=await admin_client.get("/api/agents/not-a-uuid/tasks"),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_update_agent_by_invalid_uuid_returns_422(admin_client):
    """PATCH /api/agents/{id} with non-UUID4 string returns 422."""
    validate_response(
        test_response=await admin_client.patch(
            "/api/agents/not-a-uuid",
            json={"name": "new-name"},
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_task_agent_by_invalid_uuid_returns_422(admin_client):
    """POST /api/agents/{id}/tasks with non-UUID4 agent_id returns 422."""
    validate_response(
        test_response=await admin_client.post(
            "/api/agents/not-a-uuid/tasks",
            json={"command": "shell", "arguments": {}},
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_delete_queued_agent_task_requires_admin_or_operator(
    admin_client, operator_client, client
):
    """DELETE /api/agents/{id}/tasks/queued/{task_id}: 403 spectators, 404 others."""
    fake_agent_id = "00000000-0000-4000-8000-000000000015"
    fake_task_id = "00000000-0000-4000-8000-000000000016"
    if client in (admin_client, operator_client):
        validate_response(
            test_response=await client.delete(
                f"/api/agents/{fake_agent_id}/tasks/queued/{fake_task_id}"
            ),
            expected_json_schema=AGENT_NOT_FOUND_ERROR_JSON_SCHEMA,
            expected_status_code=404,
        )
    else:
        validate_response(
            test_response=await client.delete(
                f"/api/agents/{fake_agent_id}/tasks/queued/{fake_task_id}"
            ),
            expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
            expected_status_code=403,
        )


async def test_delete_queued_agent_task_by_invalid_uuid_returns_422(admin_client):
    """DELETE /api/agents/{agent_id}/tasks/queued/{task_id} with non-UUID4 returns 422."""
    validate_response(
        test_response=await admin_client.delete(
            "/api/agents/not-a-uuid/tasks/queued/00000000-0000-4000-8000-000000000016"
        ),
        expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


# ---------------------------------------------------------------------------
# Tests that require a connected mock agent
# ---------------------------------------------------------------------------


async def test_get_all_agents_returns_connected_agent(admin_client, mock_agent):
    """GET /api/agents/all lists the registered mock agent."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await admin_client.get("/api/agents/all"),
        expected_json_schema=ALL_AGENTS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: any(a["agent_id"] == agent_id for a in r.json()),
    )


async def test_get_agent_by_id_returns_agent(admin_client, mock_agent):
    """GET /api/agents/{agent_id} returns the agent details."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await admin_client.get(f"/api/agents/{agent_id}"),
        expected_json_schema=AGENT_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json()["agent_id"] == agent_id,
    )


async def test_get_agent_tasks_by_agent_id_returns_empty_list_initially(
    admin_client, mock_agent
):
    """GET /api/agents/{agent_id}/tasks returns empty list before any tasks."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await admin_client.get(f"/api/agents/{agent_id}/tasks"),
        expected_json_schema=ALL_AGENT_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json() == [],
    )


async def test_task_agent_returns_task_model(admin_client, mock_agent):
    """POST /api/agents/{agent_id}/tasks with mock_cmd returns a valid AgentTaskModel."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await admin_client.post(
            f"/api/agents/{agent_id}/tasks",
            json={"command": "mock_cmd", "arguments": {}},
        ),
        expected_json_schema=AGENT_TASK_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json()["command"] == "mock_cmd",
    )


async def test_task_agent_with_unknown_capability_returns_422(admin_client, mock_agent):
    """POST /api/agents/{agent_id}/tasks with an unregistered command returns 422."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await admin_client.post(
            f"/api/agents/{agent_id}/tasks",
            json={"command": "nonexistent_cmd", "arguments": {}},
        ),
        expected_json_schema=AGENT_CAPABILITY_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_get_task_by_agent_id_and_task_id(admin_client, mock_agent):
    """GET /api/agents/{agent_id}/tasks/{task_id} returns the specific task."""
    agent_id = mock_agent["agent_id"]
    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    validate_response(
        test_response=await admin_client.get(f"/api/agents/{agent_id}/tasks/{task_id}"),
        expected_json_schema=AGENT_TASK_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json()["task_id"] == task_id,
    )


async def test_get_task_by_agent_id_and_wrong_agent_returns_404(
    admin_client, mock_agent
):
    """GET /api/agents/{other_agent_id}/tasks/{task_id} returns 404 when the task
    belongs to a different agent."""
    agent_id = mock_agent["agent_id"]
    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    other_agent_uuid = "00000000-0000-4000-8000-000000000020"
    validate_response(
        test_response=await admin_client.get(
            f"/api/agents/{other_agent_uuid}/tasks/{task_id}"
        ),
        expected_json_schema=AGENT_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_get_all_agent_tasks_includes_task_after_tasking(
    admin_client, mock_agent
):
    """GET /api/agents/tasks returns the task after it has been submitted."""
    agent_id = mock_agent["agent_id"]
    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    validate_response(
        test_response=await admin_client.get("/api/agents/tasks"),
        expected_json_schema=ALL_AGENT_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: any(t["task_id"] == task_id for t in r.json()),
    )


async def test_get_task_by_task_id_returns_task(admin_client, mock_agent):
    """GET /api/agents/tasks/{task_id} returns the task by its global task ID."""
    agent_id = mock_agent["agent_id"]
    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    validate_response(
        test_response=await admin_client.get(f"/api/agents/tasks/{task_id}"),
        expected_json_schema=AGENT_TASK_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json()["task_id"] == task_id,
    )


async def test_task_completes_and_reaches_terminal_state(admin_client, mock_agent):
    """After yielding to the event loop, the mock_cmd task reaches SUCCEEDED state."""
    agent_id = mock_agent["agent_id"]
    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    # Yield to the event loop to let the background asyncio capability task run.
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    task_response = await admin_client.get(f"/api/agents/tasks/{task_id}")
    assert task_response.status_code == 200
    assert task_response.json()["status"]["state"] == "SUCCEEDED"


async def test_get_all_agent_tasks_by_agent_id_includes_submitted_task(
    admin_client, mock_agent
):
    """GET /api/agents/{agent_id}/tasks lists the task after it is submitted."""
    agent_id = mock_agent["agent_id"]
    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    validate_response(
        test_response=await admin_client.get(f"/api/agents/{agent_id}/tasks"),
        expected_json_schema=ALL_AGENT_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: any(t["task_id"] == task_id for t in r.json()),
    )


async def test_update_agent_name(admin_client, mock_agent):
    """PATCH /api/agents/{agent_id} with a new name updates the agent."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await admin_client.patch(
            f"/api/agents/{agent_id}",
            json={"name": "updated-name"},
        ),
        expected_json_schema=AGENT_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json()["name"] == "updated-name",
    )


async def test_update_agent_description(admin_client, mock_agent):
    """PATCH /api/agents/{agent_id} with a new description updates the agent."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await admin_client.patch(
            f"/api/agents/{agent_id}",
            json={"description": "updated description"},
        ),
        expected_json_schema=AGENT_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda r: r.json()["description"] == "updated description",
    )


async def test_update_agent_returns_404_for_unknown_agent(admin_client, mock_agent):
    """PATCH /api/agents/{agent_id} with an unknown agent ID returns 404."""
    fake_uuid = "00000000-0000-4000-8000-000000000030"
    validate_response(
        test_response=await admin_client.patch(
            f"/api/agents/{fake_uuid}",
            json={"name": "some-name"},
        ),
        expected_json_schema=AGENT_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_queued_task_returns_204(admin_client, mock_agent):
    """DELETE /api/agents/{agent_id}/tasks/queued/{task_id} removes a QUEUED task."""
    agent_id = mock_agent["agent_id"]

    # mock_blocking_cmd keeps the task in QUEUED state (never transitions to RUNNING).
    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_blocking_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    validate_response(
        test_response=await admin_client.delete(
            f"/api/agents/{agent_id}/tasks/queued/{task_id}"
        ),
        expected_status_code=204,
    )


async def test_delete_queued_task_makes_task_unretrievable(admin_client, mock_agent):
    """After DELETE of a QUEUED task, GET /api/agents/tasks/{task_id} returns 404."""
    agent_id = mock_agent["agent_id"]

    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_blocking_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    delete_response = await admin_client.delete(
        f"/api/agents/{agent_id}/tasks/queued/{task_id}"
    )
    assert delete_response.status_code == 204

    validate_response(
        test_response=await admin_client.get(f"/api/agents/tasks/{task_id}"),
        expected_json_schema=AGENT_TASK_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_non_queued_task_returns_404(admin_client, mock_agent):
    """DELETE /api/agents/{agent_id}/tasks/queued/{task_id} on a SUCCEEDED task
    returns 404 because only QUEUED tasks can be deleted via this endpoint."""
    agent_id = mock_agent["agent_id"]

    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    # Let the mock capability run to completion (SUCCEEDED).
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    validate_response(
        test_response=await admin_client.delete(
            f"/api/agents/{agent_id}/tasks/queued/{task_id}"
        ),
        expected_json_schema=AGENT_TASK_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_spectator_cannot_update_agent(spectator_client, mock_agent):
    """PATCH /api/agents/{agent_id} returns 403 for spectator role."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await spectator_client.patch(
            f"/api/agents/{agent_id}",
            json={"name": "spectator-attempt"},
        ),
        expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
        expected_status_code=403,
    )


async def test_spectator_cannot_task_agent(spectator_client, mock_agent):
    """POST /api/agents/{agent_id}/tasks returns 403 for spectator role."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await spectator_client.post(
            f"/api/agents/{agent_id}/tasks",
            json={"command": "mock_cmd", "arguments": {}},
        ),
        expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
        expected_status_code=403,
    )


async def test_spectator_cannot_delete_queued_task(
    admin_client, spectator_client, mock_agent
):
    """DELETE /api/agents/{agent_id}/tasks/queued/{task_id} returns 403 for spectator."""
    agent_id = mock_agent["agent_id"]

    post_response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": "mock_blocking_cmd", "arguments": {}},
    )
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    validate_response(
        test_response=await spectator_client.delete(
            f"/api/agents/{agent_id}/tasks/queued/{task_id}"
        ),
        expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
        expected_status_code=403,
    )

    # Clean up the blocking task so the fixture teardown is clean.
    await admin_client.delete(f"/api/agents/{agent_id}/tasks/queued/{task_id}")
