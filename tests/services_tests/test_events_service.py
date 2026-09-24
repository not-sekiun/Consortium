import pytest

from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.events_service_exceptions import (
    EventHandlerAlreadyRegisteredError,
)
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


def test_unhashable_handler_leaves_both_indices_untouched():
    # The reverse index hashes the handler, so it is updated first: an unhashable
    # handler must not end up in one structure but not the other. A bound method is
    # not the case to test here, since 3.14 hashes one by its __self__'s address and
    # so never raises; a callable object that is itself unhashable still does.
    service = EventsService()

    class UnhashableHandler:
        __hash__ = None

        def __call__(self, event: Event) -> None:
            pass

    handler = UnhashableHandler()

    with pytest.raises(TypeError):
        service.register_event_handler_to_event_type(EventType.START_SERVER, handler)

    assert (
        service.get_registered_event_handlers_from_event_type(EventType.START_SERVER)
        == []
    )


def test_registering_the_same_handler_twice_is_rejected():
    service = EventsService()

    async def handler(event: Event) -> None:
        pass

    service.register_event_handler_to_event_type(EventType.START_SERVER, handler)
    with pytest.raises(EventHandlerAlreadyRegisteredError):
        service.register_event_handler_to_event_type(EventType.START_SERVER, handler)

    assert service.get_registered_event_handlers_from_event_type(
        EventType.START_SERVER
    ) == [handler]
