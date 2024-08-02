from consortium.framework.base_event_hook import BaseEventHook
from consortium.server.objects.event_objects import Event, EventType


class TestEventHook(BaseEventHook):
    name = "Test Event Hook"
    description = "Test event hook."
    authors = {"Sekiun"}
    event_types = {EventType.START_SERVER, EventType.STOP_SERVER}

    async def on_event_hook_triggered(self, event: Event) -> None:
        self.event_hook_logger.info(event)
