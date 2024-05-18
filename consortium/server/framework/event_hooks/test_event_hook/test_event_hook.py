from consortium.server.framework.base_event_hook import BaseEventHook
from consortium.server.objects.event_objects import Event


class TestEventHook(BaseEventHook):
    def __init__(self):
        super().__init__(
            name="Test Event Hook",
            description="An event hook for testing purposes.",
            authors=["Consortium"],
            event_types=[],
        )

    def run_event_hook(self, event: Event) -> None:
        pass
