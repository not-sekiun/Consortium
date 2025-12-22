from consortium.framework.framework_types import JSONObject
from consortium.framework.listeners import BaseListenerTemplate
from consortium.framework.options import SingleValueOption, validate_is_ip_address

from .listener import Listener
from .listener_type import ListenerType


class ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.consortium_reverse_tcp"
    name = "Consortium Reverse TCP Listener"
    description = (
        "The canonical Consortium listener implementation that communicates over the "
        "reverse TCP transport with a custom binary protocol."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    listener = Listener
    listener_type = ListenerType
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
            validating_function=validate_is_ip_address,
        ),
        SingleValueOption(
            name="local_port",
            description=(
                "The local port for the listener to bind to when listening for agents."
            ),
            required=True,
            default_value=1337,
            value_type=int,
            greater_than_or_equal_to=0,
            less_than_or_equal_to=65535,
        ),
    }

    def resolve_listener_name(self, parameters: JSONObject) -> str:
        return parameters["name"]

    def resolve_listener_endpoint(self, parameters: JSONObject) -> str:
        return f"{parameters['local_host']}:{parameters['local_host']}"
