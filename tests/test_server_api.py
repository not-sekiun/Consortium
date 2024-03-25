from tests.common_json_response_schemas import FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA
from tests.utils import validate_response

SERVER_VERSION_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "codename": {"type": "string"},
        "datetime_released": {"oneOf": [{"type": "string"}, {"type": "null"}]},
    },
    "required": ["version", "codename", "datetime_released"],
}
SERVER_CONFIG_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "local_host": {"type": "string"},
        "local_port": {"type": "integer"},
        "remote_host_whitelist": {"type": "array", "items": {"type": "string"}},
        "remote_host_blacklist": {"type": "array", "items": {"type": "string"}},
        "server_banner": {"type": "string"},
    },
}


def test_get_server_release(admin_session, operator_session, spectator_session):
    def run_session_test(session):
        validate_response(
            test_response=session.get("http://localhost:9999/api/server/release"),
            expected_json_schema=SERVER_VERSION_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )

    run_session_test(admin_session)
    run_session_test(operator_session)
    run_session_test(spectator_session)


def test_get_server_config_as_admin(admin_session, operator_session, spectator_session):
    def run_session_test(session):
        validate_response(
            test_response=session.get("http://localhost:9999/api/server/config"),
            expected_json_schema=SERVER_CONFIG_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )

    run_session_test(admin_session)
    run_session_test(operator_session)
    validate_response(
        test_response=spectator_session.get("http://localhost:9999/api/server/config"),
        expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=403,
    )
