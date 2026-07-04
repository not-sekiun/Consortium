"""The event hooks framework provides the building blocks for reacting to framework
events.

An event hook is implemented by subclassing
[`BaseEventHook`][consortium.framework.event_hooks.BaseEventHook] and declaring the
[`EventType`][consortium.framework.event_hooks.EventType] values it subscribes to. When
one of those events fires anywhere in the framework (server lifecycle changes, listener
and agent generator state changes, agent activity, user sessions, or resource CRUD
operations), the hook's handler is invoked with the event so it can run custom logic.
"""

from consortium.framework.event_hooks.base_event_hook import BaseEventHook
from consortium.framework.event_hooks.event_type import EventType

__all__ = ["BaseEventHook", "EventType"]
