from consortium.components.listener_profiles.consortium.http.listener import Listener
from consortium.components.listener_profiles.consortium.http.listener_type import (
    LISTENER_TYPE,
)
from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.framework_types import JSONObject
from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
from consortium.framework.options import ListValueOption, SingleValueOption


def _check_all_url_endpoints_unique(
    parameters: JSONObject,
) -> None:
    """
    Checks that the sets of the tasks, results and registration URL paths are mutually
    disjoint.
    """
    all_url_paths = (
        parameters["tasks_url_paths"]
        + parameters["results_url_paths"]
        + parameters["registration_url_paths"]
    )
    unique_elements = set()
    for element in all_url_paths:
        if element in unique_elements:
            raise OptionValueValidationError(
                f"The provided URL path '{element}' is not unique among the the tasks, "
                f"results and registration URL paths.",
            )
        unique_elements.add(element)


def _check_integer_is_a_valid_port_number(port: int) -> None:
    """
    Check that the integer provided is a valid port number between 0 and 65535.
    """
    if port not in range(0, 65536):
        raise OptionValueValidationError(
            f"The port number provided {port} is not a valid port number between 0 and "
            "65535",
        )


class ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.http_listener"
    name = "HTTP Listener"
    description = "A listener that communicates over the HTTP transport."
    version = "0.1.0"
    compatible_framework_version = ">=1.0.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    listener = Listener
    listener_type = LISTENER_TYPE
    options = {
        SingleValueOption(
            name="name",
            description="The name of the listener being created.",
            required=True,
            default_value="",
            value_type=str,
        ),
        SingleValueOption(
            name="local_host",
            description=(
                "The local host interface for the listener to bind to when "
                "listening for agents."
            ),
            required=True,
            default_value="0.0.0.0",
            value_type=str,
        ),
        SingleValueOption(
            name="local_port",
            description=(
                "The local port for the listener to bind to when listening for "
                "agents."
            ),
            required=True,
            default_value=1337,
            value_type=int,
            validating_function=_check_integer_is_a_valid_port_number,
        ),
        ListValueOption(
            name="tasks_url_paths",
            description=(
                "A list of available URL paths for agents to randomly query when "
                "obtaining tasks to run."
            ),
            required=True,
            default_value=["/tasks"],
            allow_duplicates=False,
            value_type=str,
            validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
        ),
        ListValueOption(
            name="results_url_paths",
            description=(
                "A list of available URL paths for agents to randomly submit to "
                "when returning the results of finished tasks."
            ),
            required=True,
            default_value=["/results"],
            allow_duplicates=False,
            value_type=str,
            validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
        ),
        ListValueOption(
            name="registration_url_paths",
            description=(
                "A list of available URL paths for the agent to randomly query "
                "when registering with the listener."
            ),
            required=True,
            default_value=["/register"],
            value_type=str,
            validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
        ),
    }
    validating_function = _check_all_url_endpoints_unique

    def resolve_listener_name(self, parameters: JSONObject) -> str:
        return parameters["name"]

    def resolve_listener_endpoint(self, parameters: JSONObject) -> str:
        return f"http://{parameters["local_host"]}:{parameters["local_port"]}"
