from consortium.framework.event_hooks import BaseEventHook
from consortium.framework.event_hooks.event_type import EventType


class EventHook(BaseEventHook):
    label = "consortium.tests.services.mock_event_hook_disabled"
    name = "Mock Disabled Event Hook"
    description = "Disabled event hook for loader tests."
    version = "0.1.0"
    authors = {"test"}
    event_types = {EventType.AGENT_REGISTERED}

    async def on_triggered(self, event):
        pass
