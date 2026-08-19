# Mock components for every user of the metadata declaration system, one module per
# domain. Each declares its metadata the way a component author would, so importing this
# package runs the real class definition time validation for all five domains.
from .mock_agent_capability import MockAgentCapability
from .mock_agent_template import MockAgentGenerator, MockAgentTemplate, MockAgentType
from .mock_event_hook import MockEventHook
from .mock_listener_template import (
    MockListener,
    MockListenerTemplate,
    MockListenerType,
)
from .mock_plugin import MockPlugin

__all__ = [
    "MockAgentCapability",
    "MockAgentGenerator",
    "MockAgentTemplate",
    "MockAgentType",
    "MockEventHook",
    "MockListener",
    "MockListenerTemplate",
    "MockListenerType",
    "MockPlugin",
]
