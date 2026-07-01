# Project Setup

This guide builds a complete event hook step by step. The hook we will write is an
**Agent Activity Tracker**: it subscribes to agent lifecycle events, counts each event
type as it fires, and writes a summary report to a JSON file when the server shuts down.
By the time we reach [Complete Event Hook Example](complete-event-hook-example.md), it
will demonstrate every major event hook concept.

## Setting up the project files

Create a directory under `consortium/components/event_hooks/`:

```
consortium/components/event_hooks/agent_activity_tracker/
    manifest.json
    event_hook.py
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
