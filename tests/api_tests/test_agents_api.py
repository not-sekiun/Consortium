import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    AGENT_CAPABILITY_NOT_FOUND_ERROR_JSON_SCHEMA,
    AGENT_JSON_SCHEMA,
    AGENT_NOT_FOUND_ERROR_JSON_SCHEMA,
    ALL_AGENTS_JSON_SCHEMA,
    TASK_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


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


async def test_task_agent_returns_task_model(admin_client, mock_agent):
    """POST /api/agents/{agent_id}/tasks with mock_cmd returns a valid AgentTaskModel."""
    agent_id = mock_agent["agent_id"]
    validate_response(
        test_response=await admin_client.post(
            f"/api/agents/{agent_id}/tasks",
            json={"command": "mock_cmd", "arguments": {}},
        ),
        expected_json_schema=TASK_JSON_SCHEMA,
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
