from consortium.framework.event_hooks import BaseEventHook
from consortium.framework.event_hooks.event_type import EventType


class EventHook(BaseEventHook):
    label = "consortium.tests.services.mock_event_hook_valid"
    name = "Mock Valid Event Hook"
    description = "Valid no-op event hook for service loader tests."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"test"}
    event_types = {EventType.AGENT_REGISTERED}

    async def on_triggered(self, event):
        pass
