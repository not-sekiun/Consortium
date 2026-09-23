import pytest

from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.services.events_service import EventsService

# The events service accepts both async and sync handlers and adapts them uniformly.
# A sync handler runs inline on the event loop, but a raise from one must still be
# contained to itself rather than aborting the whole fan-out while arguments are built.


@pytest.mark.anyio
async def test_sync_handler_receives_the_event():
    service = EventsService()
    received = []

    def handler(event: Event) -> None:
        received.append(event)

    service.register_event_handler_to_event_type(EventType.START_SERVER, handler)

    await service.trigger_event(EventType.START_SERVER, message="hello")

    assert len(received) == 1
    assert received[0].message == "hello"


@pytest.mark.anyio
async def test_sync_handler_raise_does_not_stop_sibling_handlers():
    service = EventsService()
    received = []

    def failing_handler(event: Event) -> None:
        raise ValueError("boom")

    def sibling_handler(event: Event) -> None:
        received.append(event)

    service.register_event_handler_to_event_type(
        EventType.START_SERVER, failing_handler
    )
    service.register_event_handler_to_event_type(
        EventType.START_SERVER, sibling_handler
    )

    with pytest.raises(ExceptionGroup) as exc_info:
        await service.trigger_event(EventType.START_SERVER)

    # The sibling still ran despite the other handler raising.
    assert len(received) == 1
    assert any(isinstance(error, ValueError) for error in exc_info.value.exceptions)
