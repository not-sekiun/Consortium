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
    },
    "required": ["agent_id", "name", "description"],
}
ALL_AGENTS_JSON_SCHEMA = {
    "type": "array",
    "items": AGENT_JSON_SCHEMA,
}
AGENT_TASK_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
    },
    "required": ["task_id"],
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
    """DELETE /api/agents/{id}/tasks/queued/{task_id} → 403 spectators, 404 others."""
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
