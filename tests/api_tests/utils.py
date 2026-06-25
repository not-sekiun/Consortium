import json
from collections.abc import Callable

import httpx
import jsonschema
import pytest


def _format_request_info(test_response: httpx.Response) -> str:
    try:
        request = test_response.request
        return f"{request.method} {request.url}"
    except RuntimeError:
        return "<no request available>"


def _format_response_body(test_response: httpx.Response) -> str:
    try:
        return json.dumps(test_response.json(), indent=2, sort_keys=True)
    except json.JSONDecodeError, ValueError:
        return test_response.text


def validate_response(
    test_response: httpx.Response,
    expected_json_schema: dict | None = None,
    expected_status_code: int | None = None,
    validator_function: Callable | None = None,
) -> httpx.Response:
    request_info = _format_request_info(test_response)
    formatted_body = _format_response_body(test_response)

    if expected_status_code is not None:
        if test_response.status_code != expected_status_code:
            raise AssertionError(
                f"Failed to assert response status code. Expected status code "
                f"'{expected_status_code}' but got status code {test_response.status_code}.\n"
                f"Request: {request_info}\n"
                f"Response data:\n{formatted_body}"
            )

    if expected_json_schema is not None:
        try:
            jsonschema.validate(test_response.json(), expected_json_schema)
        except jsonschema.exceptions.ValidationError as exc:
            pytest.fail(
                f"{exc.message}\n"
                f"Request: {request_info}\n"
                f"Response data:\n{formatted_body}"
            )
        except Exception as exc:
            pytest.fail(
                f"Failed to decode response as JSON. Error: {exc}.\n"
                f"Request: {request_info}\n"
                f"Response data:\n{formatted_body}"
            )

    if validator_function is not None:
        assert validator_function(test_response), (
            f"Failed to assert response with custom validator function.\n"
            f"Request: {request_info}\n"
            f"Response data:\n{formatted_body}"
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
