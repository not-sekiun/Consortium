# Event Hook Metadata

A valid event hook requires a class inheriting from `BaseEventHook` with the required
metadata attributes and an `event_types` class attribute declaring which events it
subscribes to:

```python
from consortium.framework.event_hooks import BaseEventHook, EventType


class EventHook(BaseEventHook):
    label = "consortium.event_hooks.agent_activity_tracker"
    name = "Agent Activity Tracker"
    description = (
        "Counts agent lifecycle events and writes a session summary "
        "to a JSON file on teardown."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Your Name"}
    event_types = {
        EventType.AGENT_REGISTERED,
        EventType.AGENT_CHECKED_IN,
        EventType.AGENT_TASKED,
        EventType.AGENT_TASK_COMPLETED,
        EventType.AGENT_DEREGISTERED,
    }
```

## event_types

`event_types` is a set of `EventType` values declaring what the hook subscribes to when
it is loaded. The framework only calls `on_triggered()` for events whose type the hook
is subscribed to. If `event_types` is empty or not declared, the hook is registered but
`on_triggered()` is never called unless it subscribes to something at runtime.

The declaration is read off the class, before any instance exists, so it is fixed once
the class is defined. To change subscriptions while the hook is running, call
`subscribe_to_event_type()` in `on_setup()` based on loaded configuration, as
`webhook_sender` does:

```python
# From consortium/components/event_hooks/webhook_sender/event_hook.py
for event in config["events"]:
    if event not in EventType:
        self.logger.warning("'{}' is not a valid event type.", event)
        continue
    self.subscribe_to_event_type(event)
```

## subscribed_event_types

`event_types` is the declaration; `self.subscribed_event_types` is what the hook is
actually subscribed to right now. It starts as the declared set and reflects every
`subscribe_to_event_type()` and `unsubscribe_from_event_type()` call.

It is a read-only `frozenset`, so it cannot be mutated or reassigned. Those two methods
are the only supported way to change subscriptions: a set that dispatch does not read
back would silently disagree with what the hook actually receives.

`EventType` is a `StrEnum`, so its values compare equal to their string representations.
String literals work anywhere an `EventType` is expected.

Continue to [Event Hook Setup](event-hook-setup.md) to add one-time setup logic.
