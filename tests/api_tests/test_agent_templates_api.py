import pytest
import requests

from tests.api_tests.common_json_response_schemas import (
    FORBIDDEN_ERROR_JSON_SCHEMA,
)
from tests.api_tests.framework_components_json_response_schemas import (
    AGENT_GENERATOR_JSON_SCHEMA,
    AGENT_TEMPLATE_JSON_SCHEMA,
    AGENT_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
    ALL_AGENT_TEMPLATES_JSON_SCHEMA,
)
from tests.api_tests.utils import get_all_agent_template_ids, validate_response


def test_get_all_agent_templates(
    session: requests.Session,
):
    validate_response(
        test_response=session.get(
            "http://localhost:9999/api/agent-templates/all",
        ),
        expected_json_schema=ALL_AGENT_TEMPLATES_JSON_SCHEMA,
        expected_status_code=200,
    )


def test_get_agent_template_by_agent_template_id(
    admin_session: requests.Session,
    session: requests.Session,
):
    for agent_template_id in get_all_agent_template_ids(
        admin_session,
    ):
        validate_response(
            test_response=session.get(
                f"http://localhost:9999/api/agent-templates/{agent_template_id}",
            ),
            expected_json_schema=AGENT_TEMPLATE_JSON_SCHEMA,
            expected_status_code=200,
        )

    validate_response(
        test_response=session.get(
            "http://localhost:9999/api/agent-templates/invalid-listener-template-id",
        ),
        expected_json_schema=AGENT_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA,
        expected_status_code=404,
    )


@pytest.mark.usefixtures("delete_agent_generators_after_test")
def test_create_agent_generator_through_agent_template_by_agent_template_id(
    admin_session: requests.Session,
    spectator_session: requests.Session,
    session: requests.Session,
):
    if session != spectator_session:
        # Test for admin sessions and operator sessions.
        for agent_template_id in get_all_agent_template_ids(admin_session):
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/agent-templates/{agent_template_id}",
                    json={
                        option_name: option["default_value"]
                        for option_name, option in session.get(
                            f"http://localhost:9999/api/agent-templates/{agent_template_id}",
                        )
                        .json()["options"]
                        .items()
                    },
                ),
                expected_json_schema=AGENT_GENERATOR_JSON_SCHEMA,
                expected_status_code=201,
            )
    else:
        # Test for spectator sessions.
        for agent_template_id in get_all_agent_template_ids(admin_session):
            validate_response(
                test_response=session.post(
                    f"http://localhost:9999/api/agent-templates/{agent_template_id}",
                    json={
                        option_name: option["default_value"]
                        for option_name, option in session.get(
                            f"http://localhost:9999/api/agent-templates/{agent_template_id}",
                        )
                        .json()["options"]
                        .items()
                    },
                ),
                expected_json_schema=FORBIDDEN_ERROR_JSON_SCHEMA,
                expected_status_code=403,
            )
