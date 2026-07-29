import asyncio

import pytest

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    INVALID_UUID_ERROR_JSON_SCHEMA,
    UNPROCESSABLE_ENTITY_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

TASK_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "agent_id": {"type": "string"},
        "command": {"type": "string"},
        "arguments": {"type": "object"},
        "status": {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "error": {"type": ["object", "null"]},
            },
            "required": ["state", "error"],
        },
        "event_log": {
            "type": "object",
            "properties": {
                "current_progress": {"type": ["object", "null"]},
                "total_count": {"type": "integer"},
                "entries": {"type": "array"},
            },
            "required": ["current_progress", "total_count", "entries"],
        },
        "datetime_created": {"type": "string"},
        "datetime_started": {"type": ["string", "null"]},
        "datetime_completed": {"type": ["string", "null"]},
    },
    "required": [
        "task_id",
        "agent_id",
        "command",
        "arguments",
        "status",
        "event_log",
        "datetime_created",
        "datetime_started",
        "datetime_completed",
    ],
}
ALL_TASKS_JSON_SCHEMA = {
    "type": "array",
    "items": TASK_JSON_SCHEMA,
}


def _error_json_schema(code: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "enum": [code]},
                    "message": {"type": "string"},
                    "detail": {"type": ["object", "null"]},
                },
                "required": ["code", "message", "detail"],
            },
        },
        "required": ["error"],
    }


TASK_NOT_FOUND_ERROR_JSON_SCHEMA = _error_json_schema("TASK_NOT_FOUND")
TASK_NOT_QUEUED_ERROR_JSON_SCHEMA = _error_json_schema("TASK_NOT_QUEUED")
TASK_NOT_TERMINAL_ERROR_JSON_SCHEMA = _error_json_schema("TASK_NOT_TERMINAL")


async def _submit_task(admin_client, agent_id: str, command: str) -> dict:
    response = await admin_client.post(
        f"/api/agents/{agent_id}/tasks",
        json={"command": command, "arguments": {}},
    )
    assert response.status_code == 200
    return response.json()


async def _allow_task_to_complete() -> None:
    await asyncio.sleep(0)
    await asyncio.sleep(0)


async def test_get_all_tasks_with_unknown_agent_filter_returns_empty_list(client):
    agent_id = "00000000-0000-4000-8000-000000000011"
    validate_response(
        test_response=await client.get(f"/api/tasks/all?agent_id={agent_id}"),
        expected_json_schema=ALL_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: response.json() == [],
    )


async def test_get_task_by_unknown_id_returns_404(client):
    task_id = "00000000-0000-4000-8000-000000000012"
    validate_response(
        test_response=await client.get(f"/api/tasks/{task_id}"),
        expected_json_schema=TASK_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_unknown_task_returns_404(
    admin_client,
    operator_client,
    client,
):
    task_id = "00000000-0000-4000-8000-000000000013"
    for task_kind in ("queued", "terminal"):
        if client in (admin_client, operator_client):
            validate_response(
                test_response=await client.delete(f"/api/tasks/{task_kind}/{task_id}"),
                expected_json_schema=TASK_NOT_FOUND_ERROR_JSON_SCHEMA,
                expected_status_code=404,
            )
        else:
            validate_response(
                test_response=await client.delete(f"/api/tasks/{task_kind}/{task_id}"),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


async def test_task_routes_reject_invalid_uuid_path_params(admin_client):
    # Only path parameters are reformatted into the friendlier INVALID_UUID_ERROR
    # shape, see the uuid_parsing branch in server_exception_handlers.
    for method, path in (
        ("GET", "/api/tasks/not-a-uuid"),
        ("DELETE", "/api/tasks/queued/not-a-uuid"),
        ("DELETE", "/api/tasks/terminal/not-a-uuid"),
    ):
        validate_response(
            test_response=await admin_client.request(method, path),
            expected_json_schema=INVALID_UUID_ERROR_JSON_SCHEMA,
            expected_status_code=422,
        )


async def test_get_all_tasks_rejects_invalid_uuid_agent_id_filter(admin_client):
    # The agent ID filter is a query parameter, so it falls through to the generic
    # request validation error rather than the path-parameter UUID reformatting.
    validate_response(
        test_response=await admin_client.get("/api/tasks/all?agent_id=not-a-uuid"),
        expected_json_schema=UNPROCESSABLE_ENTITY_ERROR_JSON_SCHEMA,
        expected_status_code=422,
    )


async def test_get_all_tasks_filters_by_agent_and_status(admin_client, mock_agent):
    agent_id = mock_agent["agent_id"]
    queued_task = await _submit_task(
        admin_client,
        agent_id=agent_id,
        command="mock_blocking_cmd",
    )
    succeeded_task = await _submit_task(
        admin_client,
        agent_id=agent_id,
        command="mock_cmd",
    )
    await _allow_task_to_complete()

    validate_response(
        test_response=await admin_client.get("/api/tasks/all"),
        expected_json_schema=ALL_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: {
            queued_task["task_id"],
            succeeded_task["task_id"],
        }.issubset({task["task_id"] for task in response.json()}),
    )
    validate_response(
        test_response=await admin_client.get(f"/api/tasks/all?agent_id={agent_id}"),
        expected_json_schema=ALL_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: {
            task["task_id"] for task in response.json()
        }
        == {queued_task["task_id"], succeeded_task["task_id"]},
    )
    validate_response(
        test_response=await admin_client.get("/api/tasks/all?status=QUEUED"),
        expected_json_schema=ALL_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: queued_task["task_id"]
        in {task["task_id"] for task in response.json()},
    )
    validate_response(
        test_response=await admin_client.get(
            f"/api/tasks/all?agent_id={agent_id}&status=SUCCEEDED"
        ),
        expected_json_schema=ALL_TASKS_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: {
            task["task_id"] for task in response.json()
        }
        == {succeeded_task["task_id"]},
    )

    await admin_client.delete(f"/api/tasks/queued/{queued_task['task_id']}")
    await admin_client.delete(f"/api/tasks/terminal/{succeeded_task['task_id']}")


async def test_get_task_by_task_id_returns_task(admin_client, mock_agent):
    task = await _submit_task(
        admin_client,
        agent_id=mock_agent["agent_id"],
        command="mock_blocking_cmd",
    )

    validate_response(
        test_response=await admin_client.get(f"/api/tasks/{task['task_id']}"),
        expected_json_schema=TASK_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: (
            response.json()["task_id"] == task["task_id"]
        ),
    )

    await admin_client.delete(f"/api/tasks/queued/{task['task_id']}")


async def test_delete_queued_task_returns_204_and_removes_record(
    admin_client,
    mock_agent,
):
    task = await _submit_task(
        admin_client,
        agent_id=mock_agent["agent_id"],
        command="mock_blocking_cmd",
    )

    validate_response(
        test_response=await admin_client.delete(f"/api/tasks/queued/{task['task_id']}"),
        expected_status_code=204,
    )
    validate_response(
        test_response=await admin_client.get(f"/api/tasks/{task['task_id']}"),
        expected_json_schema=TASK_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_concurrent_queued_deletes_do_not_return_500(
    admin_client,
    mock_agent,
):
    task = await _submit_task(
        admin_client,
        agent_id=mock_agent["agent_id"],
        command="mock_blocking_cmd",
    )

    responses = await asyncio.gather(
        admin_client.delete(f"/api/tasks/queued/{task['task_id']}"),
        admin_client.delete(f"/api/tasks/queued/{task['task_id']}"),
    )

    assert all(response.status_code in {204, 404} for response in responses)
    assert any(response.status_code == 204 for response in responses)
    validate_response(
        test_response=await admin_client.get(f"/api/tasks/{task['task_id']}"),
        expected_json_schema=TASK_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_terminal_task_returns_204_and_removes_record(
    admin_client,
    mock_agent,
):
    task = await _submit_task(
        admin_client,
        agent_id=mock_agent["agent_id"],
        command="mock_cmd",
    )
    await _allow_task_to_complete()

    validate_response(
        test_response=await admin_client.delete(
            f"/api/tasks/terminal/{task['task_id']}"
        ),
        expected_status_code=204,
    )
    validate_response(
        test_response=await admin_client.get(f"/api/tasks/{task['task_id']}"),
        expected_json_schema=TASK_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_delete_succeeded_task_through_queued_route_returns_409(
    admin_client,
    mock_agent,
):
    task = await _submit_task(
        admin_client,
        agent_id=mock_agent["agent_id"],
        command="mock_cmd",
    )
    await _allow_task_to_complete()

    validate_response(
        test_response=await admin_client.delete(f"/api/tasks/queued/{task['task_id']}"),
        expected_json_schema=TASK_NOT_QUEUED_ERROR_JSON_SCHEMA,
        expected_status_code=409,
    )

    await admin_client.delete(f"/api/tasks/terminal/{task['task_id']}")


async def test_delete_queued_task_through_terminal_route_returns_409(
    admin_client,
    mock_agent,
):
    task = await _submit_task(
        admin_client,
        agent_id=mock_agent["agent_id"],
        command="mock_blocking_cmd",
    )

    validate_response(
        test_response=await admin_client.delete(
            f"/api/tasks/terminal/{task['task_id']}"
        ),
        expected_json_schema=TASK_NOT_TERMINAL_ERROR_JSON_SCHEMA,
        expected_status_code=409,
    )

    await admin_client.delete(f"/api/tasks/queued/{task['task_id']}")


async def test_task_remains_queryable_after_owning_agent_is_deleted(
    admin_client,
    mock_agent,
):
    agent_id = mock_agent["agent_id"]
    task = await _submit_task(
        admin_client,
        agent_id=agent_id,
        command="mock_blocking_cmd",
    )

    delete_response = await admin_client.delete(f"/api/agents/{agent_id}")
    assert delete_response.status_code == 204

    validate_response(
        test_response=await admin_client.get(f"/api/tasks/{task['task_id']}"),
        expected_json_schema=TASK_JSON_SCHEMA,
        expected_status_code=200,
        validator_function=lambda response: (
            response.json()["status"]["state"] == "ERRORED"
            and "deleted by an operator"
            in response.json()["status"]["error"]["message"]
        ),
    )

    await admin_client.delete(f"/api/tasks/terminal/{task['task_id']}")
