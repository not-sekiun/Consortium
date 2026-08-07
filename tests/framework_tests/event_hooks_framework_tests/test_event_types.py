import pytest

from consortium.framework.event_hooks import BaseEventHook
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.events_service_exceptions import (
    InvalidEventTypeError,
)


def _make_event_hook_class(event_types=None, label="test.event_hook"):
    namespace = {
        "label": label,
        "name": "Test Event Hook",
        "description": "Event hook used to exercise the event_types contract.",
        "version": "0.1.0",
        "compatible_framework_version": ">=0.1.0a1",
        "authors": {"test"},
    }
    if event_types is not None:
        namespace["event_types"] = event_types
    return type("EventHook", (BaseEventHook,), namespace)


# --- Declaration ---


def test_class_access_returns_the_declared_event_types():
    # Metadata validation reads event_types off the class before any instance exists.
    hook_class = _make_event_hook_class({"START_SERVER"})
    assert hook_class.event_types == {"START_SERVER"}


def test_undeclared_event_types_defaults_to_an_empty_set_on_the_class():
    assert _make_event_hook_class().event_types == set()


def test_declaration_is_the_starting_subscription():
    hook = _make_event_hook_class({"START_SERVER"})()
    assert hook.subscribed_event_types == {EventType.START_SERVER}


def test_undeclared_event_types_subscribes_to_nothing():
    hook = _make_event_hook_class()()
    assert hook.subscribed_event_types == frozenset()


def test_a_subclass_inherits_the_declaration_of_its_parent():
    parent = _make_event_hook_class({"START_SERVER"}, label="test.parent")
    child_class = type(
        "ChildEventHook",
        (parent,),
        {"label": "test.child", "name": "Child Event Hook"},
    )
    assert child_class().subscribed_event_types == {EventType.START_SERVER}


def test_instances_do_not_share_the_declared_set():
    hook_class = _make_event_hook_class({"START_SERVER"})
    first, second = hook_class(), hook_class()
    first.subscribe_to_event_type(EventType.PAYLOAD_CREATED)
    assert second.subscribed_event_types == {EventType.START_SERVER}
    assert hook_class.event_types == {"START_SERVER"}


# --- Read-only view ---


def test_view_is_immutable():
    hook = _make_event_hook_class({"START_SERVER"})()
    assert isinstance(hook.subscribed_event_types, frozenset)
    with pytest.raises(AttributeError):
        hook.subscribed_event_types.add(EventType.PAYLOAD_CREATED)


def test_view_cannot_be_rebound():
    hook = _make_event_hook_class({"START_SERVER"})()
    with pytest.raises(AttributeError):
        hook.subscribed_event_types = {EventType.PAYLOAD_CREATED}


# --- Runtime subscription ---


def test_subscribe_updates_the_view():
    hook = _make_event_hook_class({"START_SERVER"})()
    hook.subscribe_to_event_type(EventType.PAYLOAD_CREATED)
    assert hook.subscribed_event_types == {
        EventType.START_SERVER,
        EventType.PAYLOAD_CREATED,
    }


def test_subscribing_does_not_change_the_declaration():
    hook_class = _make_event_hook_class({"START_SERVER"})
    hook_class().subscribe_to_event_type(EventType.PAYLOAD_CREATED)
    assert hook_class.event_types == {"START_SERVER"}


def test_unsubscribe_updates_the_view():
    hook = _make_event_hook_class({"START_SERVER"})()
    hook.unsubscribe_from_event_type(EventType.START_SERVER)
    assert hook.subscribed_event_types == frozenset()


def test_subscribe_accepts_a_plain_string_and_normalizes_it():
    hook = _make_event_hook_class()()
    hook.subscribe_to_event_type("PAYLOAD_CREATED")
    assert hook.subscribed_event_types == {EventType.PAYLOAD_CREATED}


def test_subscribe_is_idempotent():
    hook = _make_event_hook_class({"START_SERVER"})()
    hook.subscribe_to_event_type(EventType.START_SERVER)
    assert hook.subscribed_event_types == {EventType.START_SERVER}


def test_unsubscribe_from_an_unhandled_event_type_is_a_no_op():
    hook = _make_event_hook_class({"START_SERVER"})()
    hook.unsubscribe_from_event_type(EventType.PAYLOAD_CREATED)
    assert hook.subscribed_event_types == {EventType.START_SERVER}


def test_subscribe_rejects_an_invalid_event_type():
    hook = _make_event_hook_class()()
    with pytest.raises(InvalidEventTypeError):
        hook.subscribe_to_event_type("NOT_AN_EVENT_TYPE")
    assert hook.subscribed_event_types == frozenset()
