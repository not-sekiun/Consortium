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

`event_types` is a set of `EventType` values. The framework only calls `on_triggered()`
for events whose type is in this set. If `event_types` is empty or not declared, the
hook is registered but `on_triggered()` is never called.

You can also add to `event_types` dynamically in `on_setup()` based on loaded
configuration, as `webhook_sender` does:

```python
# From consortium/components/event_hooks/webhook_sender/event_hook.py
for event in config["events"]:
    if event not in EventType:
        self.logger.warning("'{}' is not a valid event type.", event)
        continue
    self.event_types.add(event)
```

`EventType` is a `StrEnum`, so its values compare equal to their string representations.
String literals work anywhere an `EventType` is expected.

Continue to [Event Hook Setup](event-hook-setup.md) to add one-time setup logic.
