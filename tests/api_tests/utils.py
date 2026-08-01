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


# The bodies of the two template creation endpoints. A created object's `name` and
# `description` are display metadata and are therefore fields of their own, separate from
# `options` which carries the creating template's option values. A template is free to
# declare its own option called `name` or `description`: those belong in `options` and are
# never conflated with the fields here. Omitting `name` leaves the server to generate one.
def build_create_request_body(
    options: dict,
    name: str | None = None,
    description: str = "",
) -> dict:
    return {"options": options, "name": name, "description": description}


async def create_listener_from_template(
    admin_client: httpx.AsyncClient,
    listener_template_id: str,
    option_overrides: dict | None = None,
    name: str | None = None,
    description: str = "",
) -> httpx.Response:
    template = (
        await admin_client.get(f"/api/listener-templates/{listener_template_id}")
    ).json()
    options = {
        option_name: option["default_value"]
        for option_name, option in template["options"].items()
    }
    options.update(option_overrides or {})
    return await admin_client.post(
        f"/api/listener-templates/{listener_template_id}",
        json=build_create_request_body(
            options=options,
            name=name,
            description=description,
        ),
    )


async def create_agent_generator_from_template(
    admin_client: httpx.AsyncClient,
    agent_template_id: str,
    option_overrides: dict | None = None,
    name: str | None = None,
    description: str = "",
) -> httpx.Response:
    template = (
        await admin_client.get(f"/api/agent-templates/{agent_template_id}")
    ).json()
    options = {
        option_name: option["default_value"]
        for option_name, option in template["options"].items()
    }
    options.update(option_overrides or {})
    return await admin_client.post(
        f"/api/agent-templates/{agent_template_id}",
        json=build_create_request_body(
            options=options,
            name=name,
            description=description,
        ),
    )


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
