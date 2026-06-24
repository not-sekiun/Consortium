from collections.abc import Callable

import httpx
import jsonschema
import pytest


def validate_response(
    test_response: httpx.Response,
    expected_json_schema: dict | None = None,
    expected_status_code: int | None = None,
    validator_function: Callable | None = None,
) -> httpx.Response:
    if expected_status_code is not None:
        assert test_response.status_code == expected_status_code, (
            f"Failed to assert response status code. Expected status code "
            f"'{expected_status_code}' but got status code {test_response.status_code}. "
            f"Response data: {test_response.text}"
        )
    if expected_json_schema is not None:
        try:
            jsonschema.validate(test_response.json(), expected_json_schema)
        except jsonschema.exceptions.ValidationError as exc:
            pytest.fail(f"{exc.message} Response data: {test_response.text}")
        except Exception as exc:
            pytest.fail(
                f"Failed to decode response as JSON. Error: {exc}. "
                f"Response data: {test_response.text}",
            )
    if validator_function is not None:
        assert validator_function(test_response), (
            f"Failed to assert response with custom validator function. "
            f"Response data: {test_response.text}"
        )
    return test_response


async def get_all_listener_template_ids(admin_client: httpx.AsyncClient) -> list[str]:
    response = await admin_client.get("/api/listener-templates/all")
    return [lt["listener_template_id"] for lt in response.json()]


async def get_all_listener_ids(admin_client: httpx.AsyncClient) -> list[str]:
    response = await admin_client.get("/api/listeners/all")
    return [listener["listener_id"] for listener in response.json()]


async def get_all_user_account_ids(admin_client: httpx.AsyncClient) -> list[str]:
    response = await admin_client.get("/api/user-accounts/all")
    return [ua["user_account_id"] for ua in response.json()]


async def get_all_agent_template_ids(admin_client: httpx.AsyncClient) -> list[str]:
    response = await admin_client.get("/api/agent-templates/all")
    return [at["agent_template_id"] for at in response.json()]


async def get_all_agent_generator_ids(admin_client: httpx.AsyncClient) -> list[str]:
    response = await admin_client.get("/api/agent-generators/all")
    return [ag["agent_generator_id"] for ag in response.json()]
