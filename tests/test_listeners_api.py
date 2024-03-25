from tests.common_json_response_schemas import SUCCESS_RESPONSE_JSON_SCHEMA
from tests.utils import validate_response

LISTENER_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "endpoint": {"type": "string"},
        "listener_type": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "listener_type_id": {"type": "string"},
            },
        },
        "authors": {"type": "array", "items": {"type": "string"}},
        "listener_id": {"type": "string"},
        "options": {"type": "object"},
        "status": {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "error": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["type", "message"],
                        },
                    ],
                },
            },
            "required": ["state"],
        },
    },
    "required": [
        "name",
        "endpoint",
        "listener_type",
        "listener_id",
        "options",
        "status",
    ],
}
ALL_LISTENERS_RESPONSE_JSON_SCHEMA = {
    "type": "array",
    "items": LISTENER_RESPONSE_JSON_SCHEMA,
}


def test_get_all_listeners_info(operator_session):
    validate_response(
        test_response=operator_session.get(
            "http://localhost:9999/api/listeners/all",
        ),
        expected_json_schema=ALL_LISTENERS_RESPONSE_JSON_SCHEMA,
        expected_status_code=200,
    )


def test_get_listener_info_by_listener_id(operator_session):
    all_listener_ids = [
        listener["listener_id"]
        for listener in operator_session.get(
            "http://localhost:9999/api/listeners/all",
        ).json()
    ]
    for listener_id in all_listener_ids:
        validate_response(
            test_response=operator_session.get(
                f"http://localhost:9999/api/listeners/{listener_id}",
            ),
            expected_json_schema=LISTENER_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )


def test_start_listener_by_listener_id(operator_session):
    all_listener_ids = [
        listener["listener_id"]
        for listener in operator_session.get(
            "http://localhost:9999/api/listeners/all",
        ).json()
    ]
    for listener_id in all_listener_ids:
        validate_response(
            test_response=operator_session.post(
                f"http://localhost:9999/api/listeners/{listener_id}/start",
            ),
            expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )


def test_stop_listener_by_listener_id(operator_session):
    all_listener_ids = [
        listener["listener_id"]
        for listener in operator_session.get(
            "http://localhost:9999/api/listeners/all",
        ).json()
    ]
    for listener_id in all_listener_ids:
        validate_response(
            test_response=operator_session.post(
                f"http://localhost:9999/api/listeners/{listener_id}/stop",
            ),
            expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )


def test_update_listener_by_listener_id(
    admin_session,
    operator_session,
    spectator_session,
):
    all_listener_ids = [
        listener["listener_id"]
        for listener in admin_session.get(
            "http://localhost:9999/api/listeners/all",
        ).json()
    ]

    def run_session_test(session):
        for listener_id in all_listener_ids:
            validate_response(
                test_response=session.put(
                    f"http://localhost:9999/api/listeners/{listener_id}",
                ),
                expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
                expected_status_code=200,
            )
