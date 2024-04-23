from consortium.server.framework.base_listener_template import BaseListenerTemplate
from consortium.server.framework.listeners.consortium.http.listener import Listener
from consortium.server.framework.listeners.consortium.http.listener_type import (
    LISTENER_TYPE,
)
from consortium.server.framework.options import ListValueOption, SingleValueOption


def _check_all_url_endpoints_unique(
    options_dict: dict[str, SingleValueOption | ListValueOption],
) -> None:
    """Checks that all the URL endpoints are unique between the tasks, results and registration URL paths"""
    all_url_paths = (
        options_dict["tasks_url_paths"].get_option_value()
        + options_dict["results_url_paths"].get_option_value()
    )
    all_url_paths.append(options_dict["registration_url_paths"])
    unique_elements = set()
    for element in all_url_paths:
        if element in unique_elements:
            raise ValueError(
                'The tasks, results and registration URL paths must not share any common URL endpoints between all of them. The URL path "{element}" violates this requirement',
            )
        unique_elements.add(element)


def _check_integer_is_a_valid_port_number(port: int) -> None:
    """Checks that the integer provided is a valid port number (0 to 65535)"""
    if port not in range(0, 65536):
        raise ValueError(
            f"The port number {port} is not a valid port number. Port numbers must be in the range of 0 to 65535",
        )


class ListenerTemplate(BaseListenerTemplate):
    def __init__(self):
        name = "HTTP Consortium Listener"
        description = "An HTTP based listener that is compatible with all Consortium-based agents (default agents bundled with the framework)"
        authors = ["Sekiun (github.com/not-sekiun)"]
        options = [
            SingleValueOption(
                name="name",
                description="Name of the listener being created.",
                required=True,
                default_value="",
                value_type=str,
            ),
            SingleValueOption(
                name="local_host",
                description="Local host interface to bind to to listen for agents.",
                required=True,
                default_value="0.0.0.0",
                value_type=str,
            ),
            SingleValueOption(
                name="local_port",
                description="Local port to bind to to listen for agents.",
                required=True,
                default_value=1337,
                value_type=int,
                validating_function=_check_integer_is_a_valid_port_number,
            ),
            ListValueOption(
                name="tasks_url_paths",
                description="URL paths for agents to make GET requests to to obtain the task to run.",
                required=True,
                default_value=["/tasks"],
                allow_duplicates=False,
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
            ListValueOption(
                name="results_url_paths",
                description="URL paths for agents to make POST requests to to return the results of tasks that were finished running.",
                required=True,
                default_value=["/results"],
                allow_duplicates=False,
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
            ListValueOption(
                name="registration_url_paths",
                description="URL paths for agents to make POST requests to to register with the listener.",
                required=True,
                default_value=["/register"],
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
        ]
        listener = Listener
        validating_function = _check_all_url_endpoints_unique
        super().__init__(
            name=name,
            description=description,
            listener_type=LISTENER_TYPE,
            authors=authors,
            options=options,
            validating_function=validating_function,
            listener=listener,
        )

    def resolve_listener_name(self) -> str:
        return self.options["name"].get_option_value()

    def resolve_listener_endpoint(self) -> str:
        return (
            "http://"
            + self.options["local_host"].get_option_value()
            + ":"
            + str(self.options["local_port"].get_option_value())
        )
