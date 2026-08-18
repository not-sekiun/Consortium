import pytest

from tests.api_tests.framework_components_json_response_schemas import (
    SERVER_CONFIG_JSON_SCHEMA,
    SERVER_VERSION_JSON_SCHEMA,
)
from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio


async def test_get_server_release(client):
    validate_response(
        test_response=await client.get("/api/server/release"),
        expected_json_schema=SERVER_VERSION_JSON_SCHEMA,
        expected_status_code=200,
    )


async def test_get_server_config(client):
    """All roles can GET /api/server/config."""
    validate_response(
        test_response=await client.get("/api/server/config"),
        expected_json_schema=SERVER_CONFIG_JSON_SCHEMA,
        expected_status_code=200,
    )
