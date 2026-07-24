# Project Setup

This guide builds a complete event hook step by step. The hook we will write is an
**Agent Activity Tracker**: it subscribes to agent lifecycle events, counts each event
type as it fires, and writes a summary report to a JSON file when the server shuts down.
By the time we reach [Complete Event Hook Example](complete-event-hook-example.md), it
will demonstrate every major event hook concept.

!!! tip "Scaffold it instead"

    Rather than creating these files by hand, you can generate a ready-to-edit event hook
    (directory, `manifest.json`, and a commented `event_hook.py`) with the **Create**
    action of the [component manager](../../../scripts/manage-components.md)
    (`manage_components.py`). This guide is still worth reading to understand what the
    generated files do.

## Setting up the project files

Create a directory under `consortium/components/event_hooks/`:

```
consortium/components/event_hooks/agent_activity_tracker/
├── manifest.json
└── event_hook.py
```

`manifest.json` points the component loader at the entry class. The entry point format
is `<module>:<class>`. The class must be named `EventHook` by convention:

```json
{
  "entry_point": "event_hook:EventHook",
  "enabled": true
}
```

Continue to [Event Hook Metadata](event-hook-metadata.md) to declare the event hook
class itself.
