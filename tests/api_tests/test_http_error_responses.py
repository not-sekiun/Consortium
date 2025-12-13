from enum import StrEnum

import jsonschema
import requests

from tests.api_tests.common_json_response_schemas import (
    METHOD_NOT_ALLOWED_ERROR_JSON_SCHEMA,
    NOT_FOUND_ERROR_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response


class _HTTPMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


# _ALL_METHODS is just used for checking membership of the _HTTPMethod enum so we use
# the set() constructor to make it more efficient to check membership.
_ALL_METHODS = set(_HTTPMethod)
# Programmatically get all the endpoints and methods from the openapi specification. For
# endpoints that require a path parameter, the path parameter is represented by the
# string of its variable. For example, "/api/listeners/{listener_id}" would be
# represented as "/api/listeners/listener_id" this is because the relevant tested errors
# (401, 405, and 422) are raised ahead of a 404. e.g. POSTing to a GET endpoint at
# /api/listeners/listener_id would raise a 405 before a 404.
_ENDPOINTS_AND_METHODS_MAP = {}
open_api_json_specification = requests.get(
    "http://localhost:9999/openapi.json",
).json()
str_methods_to_enum_methods = {
    "get": _HTTPMethod.GET,
    "post": _HTTPMethod.POST,
    "put": _HTTPMethod.PUT,
    "delete": _HTTPMethod.DELETE,
    "patch": _HTTPMethod.PATCH,
    "options": _HTTPMethod.OPTIONS,
}
for open_api_path in open_api_json_specification["paths"]:
    for method in open_api_json_specification["paths"][open_api_path]:
        method_enum = str_methods_to_enum_methods[method]
        url_path = "http://localhost:9999" + open_api_path.replace("{", "").replace(
            "}",
            "",
        )
        if url_path not in _ENDPOINTS_AND_METHODS_MAP:
            _ENDPOINTS_AND_METHODS_MAP[url_path] = [method_enum]
        else:
            _ENDPOINTS_AND_METHODS_MAP[url_path].append(method_enum)


def test_unauthorized_error_response():
    requests_session = requests.Session()
    method_to_function_map = {
        _HTTPMethod.GET: requests_session.get,
        _HTTPMethod.POST: requests_session.post,
        _HTTPMethod.PUT: requests_session.put,
        _HTTPMethod.DELETE: requests_session.delete,
        _HTTPMethod.PATCH: requests_session.patch,
        _HTTPMethod.OPTIONS: requests_session.options,
    }

    for endpoint, supported_methods_list in _ENDPOINTS_AND_METHODS_MAP.items():
        for supported_method in supported_methods_list:
            validate_response(
                test_response=method_to_function_map[supported_method](endpoint),
                expected_status_code=401,
                validator_function=lambda response: not response.content,
            )


def test_not_found_error_response(admin_session: requests.Session):
    validate_response(
        test_response=admin_session.get("http://localhost:9999/does-not-exist"),
        expected_json_schema=NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


def test_method_not_allowed_error_response(
    admin_session: requests.Session,
):
    method_to_function_map = {
        _HTTPMethod.GET: admin_session.get,
        _HTTPMethod.POST: admin_session.post,
        _HTTPMethod.PUT: admin_session.put,
        _HTTPMethod.DELETE: admin_session.delete,
        _HTTPMethod.PATCH: admin_session.patch,
        _HTTPMethod.OPTIONS: admin_session.options,
    }

    for endpoint, supported_methods_list in _ENDPOINTS_AND_METHODS_MAP.items():
        for test_method in _ALL_METHODS:
            if test_method not in supported_methods_list:
                response = method_to_function_map[test_method](endpoint)

                # 404s will occur when a test path coincidentally matches a
                # parameterized path. For example, consider the two valid endpoints,
                # GET /api/user-accounts/all and DELETE
                # /api/user-accounts/{user_id}. When we attempt to test GET
                # /api/user-accounts/all with an invalid DELETE method, the server
                # is interpreting it as a DELETE request with "all" as the path
                # parameter. This will result in a 404 error or 422 where data
                # needs to be POSTed in the request body.
                if response.status_code in (404, 422):
                    continue

                # Make assertions without the validate_response function to
                # avoid duplicate requests being sent to the server.
                assert response.status_code == 405
                try:
                    jsonschema.validate(
                        response.json(),
                        METHOD_NOT_ALLOWED_ERROR_JSON_SCHEMA,
                    )
                except jsonschema.ValidationError as exc:
                    raise AssertionError(
                        f"Response JSON schema did not match expected schema. {exc}",
                    ) from None
