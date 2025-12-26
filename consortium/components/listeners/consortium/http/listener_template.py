from consortium.framework.exceptions import (
    OptionValueValidationError,
)
from consortium.framework.framework_types import JSONObject
from consortium.framework.listeners import BaseListenerTemplate
from consortium.framework.options import (
    ListValueOption,
    SingleValueOption,
    validate_is_ip_address,
    validate_is_url_path,
)

from .listener import Listener
from .listener_type import ListenerType


def _validate_all_url_endpoints_unique(
    parameters: JSONObject,
) -> None:
    """
    Validates that the sets of the tasks, results, and registration URL paths are
    mutually disjoint.
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
                f"The provided URL path '{element}' is not unique among the tasks, "
                f"results, and registration URL paths.",
            )
        unique_elements.add(element)


class ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.consortium_http"
    name = "Consortium HTTP Listener"
    description = (
        "The canonical Consortium listener implementation that communicates over the "
        "HTTP transport with a custom JSON-based protocol."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    listener = Listener
    listener_type = ListenerType
    options = {
        SingleValueOption(
            name="name",
            description="Name of the listener being created.",
            required=True,
            default_value="",
            value_type=str,
        ),
        SingleValueOption(
            name="local_host",
            description=(
                "Local host interface for the listener to bind to when "
                "listening for agents."
            ),
            required=True,
            default_value="0.0.0.0",
            value_type=str,
            validating_function=validate_is_ip_address,
        ),
        SingleValueOption(
            name="local_port",
            description=(
                "Local port for the listener to bind on when listening for agents."
            ),
            required=True,
            default_value=1337,
            value_type=int,
            greater_than_or_equal_to=0,
            less_than_or_equal_to=65535,
        ),
        ListValueOption(
            name="tasks_url_paths",
            description=("List of available URL paths for agents to query tasks from."),
            required=True,
            default_value=["/tasks"],
            allow_duplicates=False,
            value_type=str,
            validating_function=validate_is_url_path,
        ),
        ListValueOption(
            name="results_url_paths",
            description=(
                "List of available URL paths for agents to submit results to."
            ),
            required=True,
            default_value=["/results"],
            allow_duplicates=False,
            value_type=str,
            validating_function=validate_is_url_path,
        ),
        ListValueOption(
            name="registration_url_paths",
            description=(
                "List of available URL paths for agents to submit data to when "
                "registering with the listener."
            ),
            required=True,
            default_value=["/register"],
            value_type=str,
            validating_function=validate_is_url_path,
        ),
    }
    validating_function = _validate_all_url_endpoints_unique

    def resolve_listener_name(self, parameters: JSONObject) -> str:
        return parameters["name"]

    def resolve_listener_endpoint(self, parameters: JSONObject) -> str:
        return f"http://{parameters['local_host']}:{parameters['local_port']}"
