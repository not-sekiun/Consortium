from consortium.framework.event_hooks import BaseEventHook
from consortium.framework.event_hooks.event_type import EventType


class EventHook(BaseEventHook):
    label = "consortium.tests.services.mock_event_hook_teardown_error"
    name = "Mock Teardown Error Event Hook"
    description = "Event hook whose on_teardown raises to trigger EventHookTeardownError."
    version = "0.1.0"
    authors = {"test"}
    event_types = {EventType.AGENT_REGISTERED}

    async def on_triggered(self, event):
        pass

    async def on_teardown(self):
        raise RuntimeError("deliberate on_teardown error")
