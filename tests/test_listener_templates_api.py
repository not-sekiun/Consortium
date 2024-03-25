from tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
    SUCCESS_RESPONSE_JSON_SCHEMA,
)
from tests.utils import delete_all_listeners, validate_response

LISTENER_TEMPLATE_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "listener_type": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "listener_type_id": {"type": "string"},
            },
        },
        "authors": {"type": "array", "items": {"type": "string"}},
        "options": {"type": "object"},
        "listener_template_id": {"type": "string"},
        "validating_function": {"type": ["string", "null"]},
    },
    "required": [
        "name",
        "description",
        "listener_type",
        "authors",
        "options",
        "listener_template_id",
        "validating_function",
    ],
    "additionalProperties": False,
}
ALL_LISTENER_TEMPLATES_RESPONSE_JSON_SCHEMA = {
    "type": "array",
    "items": LISTENER_TEMPLATE_RESPONSE_JSON_SCHEMA,
}
LISTENER_TEMPLATE_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["LISTENER_TEMPLATE_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


def test_get_all_listener_templates_info(
    admin_session,
    operator_session,
    spectator_session,
):
    def run_session_test(session):
        validate_response(
            test_response=session.get(
                "http://localhost:9999/api/listener_templates/all",
            ),
            expected_json_schema=ALL_LISTENER_TEMPLATES_RESPONSE_JSON_SCHEMA,
            expected_status_code=200,
        )

    run_session_test(admin_session)
    run_session_test(operator_session)
    run_session_test(spectator_session)


def test_get_listener_template_info_by_listener_template_id(
    admin_session,
    operator_session,
    spectator_session,
):
    all_listener_template_ids = [
        listener_template["listener_template_id"]
        for listener_template in operator_session.get(
            "http://localhost:9999/api/listener_templates/all",
        ).json()
    ]

    def run_session_test(session):
        for listener_template_id in all_listener_template_ids:
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/listener_templates/{listener_template_id}",
                ),
                expected_json_schema=LISTENER_TEMPLATE_RESPONSE_JSON_SCHEMA,
                expected_status_code=200,
            )

        validate_response(
            test_response=session.get(
                f"http://localhost:9999/api/listener_templates/invalid-listener-template-id",
            ),
            expected_json_schema=LISTENER_TEMPLATE_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=404,
        )

    run_session_test(admin_session)
    run_session_test(operator_session)
    run_session_test(spectator_session)


def test_create_listener_through_listener_template_by_listener_template_id(
    admin_session,
    operator_session,
    spectator_session,
):
    all_listener_template_ids = [
        listener_template["listener_template_id"]
        for listener_template in admin_session.get(
            "http://localhost:9999/api/listener_templates/all",
        ).json()
    ]

    # admin_session and operator_session tests
    def run_session_test(session):
        for listener_template_id in all_listener_template_ids:
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/listener_templates/{listener_template_id}",
                    json={
                        option_name: option["default_value"]
                        for option_name, option in session.get(
                            f"http://localhost:9999/api/listener_templates/{listener_template_id}",
                        )
                        .json()["options"]
                        .items()
                    },
                ),
                expected_json_schema=SUCCESS_RESPONSE_JSON_SCHEMA,
                expected_status_code=201,
            )

        validate_response(
            test_response=session.post(
                f"http://localhost:9999/api/listener_templates/invalid-listener-template-id",
                json={},
            ),
            expected_json_schema=LISTENER_TEMPLATE_NOT_FOUND_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=404,
        )

        # perform test cleanup
        delete_all_listeners(admin_session)

    run_session_test(admin_session)
    run_session_test(operator_session)

    # spectator_session tests
    for listener_template_id in all_listener_template_ids:
        validate_response(
            test_response=spectator_session.post(
                f"http://localhost:9999/api/listener_templates/{listener_template_id}",
                json={
                    option_name: option["default_value"]
                    for option_name, option in spectator_session.get(
                        f"http://localhost:9999/api/listener_templates/{listener_template_id}",
                    )
                    .json()["options"]
                    .items()
                },
            ),
            expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
            expected_status_code=403,
        )

    validate_response(
        test_response=spectator_session.post(
            f"http://localhost:9999/api/listener_templates/invalid-listener-template-id",
            json={},
        ),
        expected_json_schema=FORBIDDEN_ERROR_RESPONSE_JSON_SCHEMA,
        expected_status_code=403,
    )
