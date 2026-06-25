from consortium.framework.listeners import BaseListenerTemplate
from consortium.framework.options import SingleValueOption

from .listener import Listener
from .listener_type import ListenerType


class ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.mock"
    name = "Mock Listener"
    description = "A no-op listener used by API tests that does not bind to any port."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"test"}
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
    }

    def resolve_listener_name(self, parameters):
        return parameters["name"]

    def resolve_listener_endpoint(self, parameters):
        return "mock://localhost"
