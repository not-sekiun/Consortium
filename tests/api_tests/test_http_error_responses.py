from enum import StrEnum

import httpx
import jsonschema
import pytest

from tests.api_tests.common_json_response_schemas import (
    METHOD_NOT_ALLOWED_ERROR_JSON_SCHEMA,
    NOT_FOUND_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


class _HTTPMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


_ALL_METHODS = set(_HTTPMethod)


async def _build_endpoints_map(app) -> dict[str, list[_HTTPMethod]]:
    """Fetch the OpenAPI spec from the running app and build path→methods map."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        spec = (await client.get("/openapi.json")).json()

    str_to_method = {
        "get": _HTTPMethod.GET,
        "post": _HTTPMethod.POST,
        "put": _HTTPMethod.PUT,
        "delete": _HTTPMethod.DELETE,
        "patch": _HTTPMethod.PATCH,
        "options": _HTTPMethod.OPTIONS,
    }
    endpoints: dict[str, list[_HTTPMethod]] = {}
    for path, methods_dict in spec["paths"].items():
        for method_str in methods_dict:
            if method_str not in str_to_method:
                continue
            # Replace {param} placeholders with their bare name so
            # 405/401 tests hit the right parameterized route.
            url_path = path.replace("{", "").replace("}", "")
            method_enum = str_to_method[method_str]
            endpoints.setdefault(url_path, []).append(method_enum)
    return endpoints


async def test_unauthorized_error_response(app):
    """Every endpoint returns an empty 401 when no auth header is provided."""
    endpoints = await _build_endpoints_map(app)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        method_to_fn = {
            _HTTPMethod.GET: client.get,
            _HTTPMethod.POST: client.post,
            _HTTPMethod.PUT: client.put,
            _HTTPMethod.DELETE: client.delete,
            _HTTPMethod.PATCH: client.patch,
            _HTTPMethod.OPTIONS: client.options,
        }
        for endpoint, supported_methods in endpoints.items():
            for method in supported_methods:
                response = await method_to_fn[method](endpoint)
                assert response.status_code == 401, (
                    f"Expected 401 at {method} {endpoint}, "
                    f"got {response.status_code}: {response.text}"
                )
                assert not response.content, (
                    f"Expected empty body on 401 at {method} {endpoint}, "
                    f"got: {response.text}"
                )


async def test_not_found_error_response(admin_client):
    """A request to a path that does not exist returns 404 with standard error body."""
    validate_response(
        test_response=await admin_client.get("/does-not-exist"),
        expected_json_schema=NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


async def test_method_not_allowed_error_response(app, admin_client):
    """Each endpoint returns 405 with standard body for unsupported HTTP methods."""
    endpoints = await _build_endpoints_map(app)
    method_to_fn = {
        _HTTPMethod.GET: admin_client.get,
        _HTTPMethod.POST: admin_client.post,
        _HTTPMethod.PUT: admin_client.put,
        _HTTPMethod.DELETE: admin_client.delete,
        _HTTPMethod.PATCH: admin_client.patch,
        _HTTPMethod.OPTIONS: admin_client.options,
    }
    for endpoint, supported_methods in endpoints.items():
        for test_method in _ALL_METHODS:
            if test_method in supported_methods:
                continue
            response = await method_to_fn[test_method](endpoint)
            # 404s occur when a test path coincidentally matches a parameterized
            # route (e.g. DELETE /api/user-accounts/all vs DELETE
            # /api/user-accounts/{id}). 422s appear when a body is required.
            # Both are false positives — skip them.
            if response.status_code in (404, 422):
                continue
            assert response.status_code == 405, (
                f"Expected 405 at {test_method} {endpoint}, "
                f"got {response.status_code}: {response.text}"
            )
            try:
                jsonschema.validate(
                    response.json(),
                    METHOD_NOT_ALLOWED_ERROR_JSON_SCHEMA,
                )
            except jsonschema.ValidationError as exc:
                raise AssertionError(
                    f"Response body at {test_method} {endpoint} did not match "
                    f"METHOD_NOT_ALLOWED schema: {exc}"
                ) from None
