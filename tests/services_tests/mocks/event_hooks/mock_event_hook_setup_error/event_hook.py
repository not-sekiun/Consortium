from consortium.framework.event_hooks import BaseEventHook
from consortium.framework.event_hooks.event_type import EventType


class EventHook(BaseEventHook):
    label = "consortium.tests.services.mock_event_hook_setup_error"
    name = "Mock Setup Error Event Hook"
    description = "Event hook whose on_setup raises to trigger EventHookSetupError."
    version = "0.1.0"
    authors = {"test"}
    event_types = {EventType.AGENT_REGISTERED}

    async def on_setup(self):
        raise RuntimeError("deliberate on_setup error")

    async def on_triggered(self, event):
        pass
