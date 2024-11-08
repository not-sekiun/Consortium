from consortium.components.listeners.consortium.reverse_tcp.listener import Listener
from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
from consortium.framework.options import SingleValueOption


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
    name = "Reverse TCP Listener"
    description = "A listener that communicates over the reverse TCP transport."
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
    }

    def resolve_listener_name(self) -> str:
        return self.get_option_by_option_name("name").get_option_value()

    def resolve_listener_endpoint(self) -> str:
        local_host = self.get_option_by_option_name("local_host").get_option_value()
        local_port = self.get_option_by_option_name("local_port").get_option_value()
        return f"{local_host}:{local_port}"
