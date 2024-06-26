from consortium.server.framework.base_listener_template import BaseListenerTemplate
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.framework.listeners.consortium.http.listener import Listener
from consortium.server.framework.options import ListValueOption, SingleValueOption


def _check_all_url_endpoints_unique(
    options_dict: dict[str, SingleValueOption | ListValueOption],
) -> None:
    """
    Checks that the list of the tasks, results and registration URL paths are mutually
    exclusive to one another.
    """
    all_url_paths = (
        options_dict["tasks_url_paths"].get_option_value()
        + options_dict["results_url_paths"].get_option_value()
    )
    all_url_paths.append(options_dict["registration_url_paths"])
    unique_elements = set()
    for element in all_url_paths:
        if element in unique_elements:
            raise OptionValueValidationError(
                f'The provided URL path "{element}" is not unique among the the tasks, '
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
    listener = Listener
    name = "HTTP Listener"
    description = "A listener that communicates over the HTTP transport."
    authors = {"Sekiun (github.com/not-sekiun)"}
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

    def resolve_listener_name(self) -> str:
        return self.get_option_by_option_name("name").get_option_value()

    def resolve_listener_endpoint(self) -> str:
        local_host = self.get_option_by_option_name("local_host").get_option_value()
        local_port = self.get_option_by_option_name("local_port").get_option_value()
        return f"http://{local_host}:{local_port}"
