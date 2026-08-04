import pytest

from tests.api_tests.utils import validate_response

pytestmark = pytest.mark.anyio

SERVER_VERSION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "codename": {"type": "string"},
        "datetime_released": {"type": ["string", "null"]},
    },
    "required": ["version", "codename", "datetime_released"],
    "additionalProperties": False,
}
SERVER_CONFIG_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "local_host": {"type": "string"},
        "local_port": {"type": "integer"},
        "remote_host_whitelist": {"type": "array", "items": {"type": "string"}},
        "remote_host_blacklist": {"type": "array", "items": {"type": "string"}},
        "server_header": {"type": ["string", "null"]},
        "ssl_certfile": {"type": ["string", "null"]},
        "ssl_keyfile": {"type": ["string", "null"]},
    },
    "required": [
        "local_host",
        "local_port",
        "remote_host_whitelist",
        "remote_host_blacklist",
        "server_header",
        "ssl_certfile",
        "ssl_keyfile",
    ],
    "additionalProperties": False,
}


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
