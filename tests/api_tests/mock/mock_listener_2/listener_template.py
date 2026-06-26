from consortium.framework.listeners import BaseListenerTemplate
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)

from .listener import Listener
from .listener_type import ListenerType


class ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.mock_2"
    name = "Mock Listener 2"
    description = "No-op listener 2 used by API tests; does not bind to any port."
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
        SingleValueOption(
            name="max_connections",
            description="Maximum concurrent connections the listener will accept.",
            required=True,
            default_value=100,
            value_type=int,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=10000,
        ),
        SingleValueOption(
            name="keep_alive_timeout",
            description="Seconds to hold an idle connection open before closing it.",
            required=True,
            default_value=30.0,
            value_type=float,
            greater_than_or_equal_to=0.0,
        ),
        SingleValueOption(
            name="compress_responses",
            description="Compress response bodies with gzip before sending.",
            required=True,
            default_value=False,
            value_type=bool,
        ),
        ListValueOption(
            name="blocked_user_agents",
            description="User-agent strings that this listener will reject outright.",
            required=True,
            default_value=[],
            allow_duplicates=False,
            value_type=str,
        ),
        ChoiceValueOption(
            name="log_level",
            description="Verbosity level for listener-specific logging output.",
            required=True,
            default_value="warning",
            available_values={"debug", "info", "warning", "error"},
        ),
        ToggleableChoicesValueOption(
            name="security_options",
            description="Security hardening flags to apply at listener startup.",
            required=True,
            default_value={"rate_limiting": False, "ip_filtering": False},
            available_values={"rate_limiting", "ip_filtering", "tls_validation"},
        ),
        DictionaryValueOption(
            name="environment_vars",
            description="Environment variables injected into the listener process.",
            required=True,
            default_value={},
            value_type=str,
        ),
        SingleValueOption(
            name="timeout",
            description="Connection timeout in seconds.",
            required=True,
            default_value=30,
            value_type=int,
            greater_than_or_equal_to=0,
            less_than_or_equal_to=3600,
        ),
    }

    def resolve_listener_name(self, parameters):
        return parameters["name"]

    def resolve_listener_endpoint(self, parameters):
        return "mock2://localhost"
