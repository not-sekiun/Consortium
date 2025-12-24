# TODO: Use fixtures to reduce code duplication.
import uuid

import pytest
import requests

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
    SUCCESS_JSON_SCHEMA,
)
from tests.api_tests.utils import get_all_listener_ids, validate_response

LISTENER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "endpoint": {"type": "string"},
        "listener_type": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "compatible_agent_type_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "listener_type_id": {"type": "string"},
            },
        },
        "authors": {"type": "array", "items": {"type": "string"}},
        "listener_id": {"type": "string"},
        "parameters": {"type": "object"},
        "status": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
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
            "required": ["status", "error"],
        },
    },
    "required": [
        "name",
        "endpoint",
        "listener_type",
        "listener_id",
        "parameters",
        "status",
    ],
}
ALL_LISTENERS_JSON_SCHEMA = {
    "type": "array",
    "items": LISTENER_JSON_SCHEMA,
}


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
def test_get_all_listeners(
    session: requests.Session,
):
    validate_response(
        test_response=session.get(
            "http://localhost:9999/api/listeners/all",
        ),
        expected_json_schema=ALL_LISTENERS_JSON_SCHEMA,
        expected_status_code=200,
    )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
def test_get_listener_by_listener_id(
    admin_session: requests.Session,
    session: requests.Session,
):
    for listener_id in get_all_listener_ids(admin_session):
        validate_response(
            test_response=session.get(
                f"http://localhost:9999/api/listeners/{listener_id}",
            ),
            expected_json_schema=LISTENER_JSON_SCHEMA,
            expected_status_code=200,
        )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
def test_start_listener_by_listener_id(
    admin_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    if session != spectator_session:
        # Test for admin sessions and operator sessions.
        for listener_id in get_all_listener_ids(admin_session):
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/start",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
            # Listeners cannot be deleted if they are running, so we stop them first to
            # allow the fixture to properly delete the listener after the test finishes.
            validate_response(
                test_response=admin_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/stop",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
    else:
        # Test for spectator sessions.
        for listener_id in get_all_listener_ids(admin_session):
            validate_response(
                test_response=spectator_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/start",
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
def test_stop_listener_by_listener_id(
    admin_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    if session != spectator_session:
        # Test for admin sessions and operator sessions.
        for listener_id in get_all_listener_ids(admin_session):
            validate_response(
                test_response=admin_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/start",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/stop",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
    else:
        for listener_id in get_all_listener_ids(admin_session):
            # Test for spectator sessions.
            validate_response(
                test_response=admin_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/start",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
            validate_response(
                test_response=spectator_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/stop",
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            # Get the admin session to stop the listener before the fixture deletes it
            # since spectators cannot delete listeners that are running.
            validate_response(
                test_response=admin_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/stop",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
def test_cancel_listener_by_listener_id(
    admin_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    if session != spectator_session:
        # Test for admin sessions and operator sessions.
        for listener_id in get_all_listener_ids(admin_session):
            validate_response(
                test_response=admin_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/start",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/cancel",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
    else:
        for listener_id in get_all_listener_ids(admin_session):
            # Test for spectator sessions.
            validate_response(
                test_response=admin_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/start",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
            validate_response(
                test_response=spectator_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/cancel",
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            # Get the admin session to stop the listener before the fixture deletes it
            # since spectators cannot delete listeners that are running.
            validate_response(
                test_response=admin_session.post(
                    f"http://localhost:9999/api/listeners/{listener_id}/cancel",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )


@pytest.mark.usefixtures("create_listeners_before_test")
@pytest.mark.usefixtures("delete_listeners_after_test")
def test_update_listener_by_listener_id(
    admin_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    new_name = uuid.uuid4().hex
    new_description = uuid.uuid4().hex

    if session != spectator_session:
        # Test for admin sessions and operator sessions.
        for listener_id in get_all_listener_ids(admin_session):
            validate_response(
                test_response=session.put(
                    f"http://localhost:9999/api/listeners/{listener_id}",
                    json={"name": new_name, "description": new_description},
                ),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=200,
            )
            validate_response(
                test_response=session.get(
                    f"http://localhost:9999/api/listeners/{listener_id}",
                ),
                expected_json_schema=LISTENER_JSON_SCHEMA,
                expected_status_code=200,
                validator_function=lambda response: response.json()["name"] == new_name
                and response.json()["description"] == new_description,
            )
    else:
        # Test for spectator sessions.
        for listener_id in get_all_listener_ids(admin_session):
            validate_response(
                test_response=spectator_session.put(
                    f"http://localhost:9999/api/listeners/{listener_id}",
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )


@pytest.mark.usefixtures("create_listeners_before_test")
def test_delete_listener_by_listener_id(
    admin_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    if session != spectator_session:
        # Test for admin sessions and operator sessions.
        for listener_id in get_all_listener_ids(admin_session):
            validate_response(
                test_response=session.delete(
                    f"http://localhost:9999/api/listeners/{listener_id}",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
    else:
        # Test for spectator sessions.
        for listener_id in get_all_listener_ids(admin_session):
            validate_response(
                test_response=spectator_session.delete(
                    f"http://localhost:9999/api/listeners/{listener_id}",
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
            validate_response(
                test_response=admin_session.delete(
                    f"http://localhost:9999/api/listeners/{listener_id}",
                ),
                expected_json_schema=SUCCESS_JSON_SCHEMA,
                expected_status_code=200,
            )
