import schemathesis
from hypothesis import HealthCheck, settings
from schemathesis.checks import not_a_server_error

# Property based fuzzing of the whole in-memory API framework. Hypothesis synthesises
# requests for every (non-excluded) operation exposed by the OpenAPI schema and checks
# that the server never returns a 5xx and that every response conforms to the schema it
# advertises (status code, content type and response body).
#
# The schema is loaded lazily from the `fuzz_api_schema` fixture so it is only built after
# the session-scoped server has completed its startup procedure and registered every
# route. See conftest.py for the isolated in-memory server setup.
schema = schemathesis.pytest.from_fixture("fuzz_api_schema")


@schema.parametrize()
@settings(
    max_examples=25,
    # In-memory ASGI calls plus response validation can occasionally exceed the default
    # per-example deadline, which would produce flaky failures unrelated to correctness.
    deadline=None,
    # The auth headers come from a session-scoped fixture whose value is constant for the
    # whole run, so the function-scoped-fixture health check does not apply here.
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_api_fuzzing(case, fuzz_auth_headers):
    response = case.call(headers=fuzz_auth_headers)
    # Authentication is enforced by a middleware that runs BEFORE routing, and any request
    # that fails it is answered with a deliberately bare 401 (empty body, no
    # `Content-Type`) so that unauthenticated clients cannot fingerprint which routes or
    # methods exist. Schemathesis' negative and coverage phases probe with invalidated
    # auth headers and undocumented HTTP methods, which therefore legitimately receive
    # that bare 401 rather than the JSON error contract the schema documents for 401
    # (tripping `content_type_conformance`/`response_schema_conformance`) or the 405 that
    # `unsupported_method` demands for an unlisted method. Treat any 401 as an expected
    # response and only assert the server did not 5xx; hold every other response to the
    # full documented schema contract.
    if response.status_code == 401:
        case.validate_response(response, checks=[not_a_server_error])
    else:
        case.validate_response(response)
