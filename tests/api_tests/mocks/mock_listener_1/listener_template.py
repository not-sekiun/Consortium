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
    label = "consortium.listeners.mock_1"
    name = "Mock Listener 1"
    description = "No-op listener 1 used by API tests; does not bind to any port."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"test"}
    listener = Listener
    listener_type = ListenerType
    options = {
        # Deliberately named "name" to keep the tests honest: a template option called
        # "name" is an ordinary option like any other and must never be conflated with
        # the created listener's display name.
        SingleValueOption(
            name="name",
            description="Arbitrary label carried as a listener parameter.",
            required=True,
            default_value="",
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
        SingleValueOption(
            name="jitter_factor",
            description="Jitter factor for randomising beacon timing (0.0 to 1.0).",
            required=True,
            default_value=0.1,
            value_type=float,
            greater_than_or_equal_to=0.0,
            less_than_or_equal_to=1.0,
        ),
        SingleValueOption(
            name="verbose",
            description="Enable verbose debug logging for this listener.",
            required=True,
            default_value=False,
            value_type=bool,
        ),
        ListValueOption(
            name="allowed_ips",
            description="Allowlist of source IP addresses. Empty list permits all.",
            required=True,
            default_value=[],
            allow_duplicates=False,
            value_type=str,
        ),
        ChoiceValueOption(
            name="protocol",
            description="Transport protocol for the mock listener.",
            required=True,
            default_value="http",
            available_values={"http", "https", "tcp"},
        ),
        ToggleableChoicesValueOption(
            name="features",
            description="Optional feature flags for the mock listener.",
            required=True,
            default_value={"logging": False, "metrics": False},
            available_values={"logging", "metrics", "tracing"},
        ),
        DictionaryValueOption(
            name="headers",
            description="Custom key/value headers attached to mock responses.",
            required=True,
            default_value={},
            value_type=str,
        ),
    }

    # Derived from a parameter rather than returned as a constant so that the tests can
    # tell the two halves of the update path apart: the endpoint is expected to be
    # re-derived whenever the parameters change, the name is expected never to be.
    def resolve_listener_endpoint(self, parameters):
        return f"mock://localhost:{parameters['timeout']}"
