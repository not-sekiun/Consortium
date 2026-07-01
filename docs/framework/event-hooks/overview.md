# Event Hooks

An event hook is a component that reacts to specific framework events. Unlike plugins,
which run continuously in the background, event hooks are driven entirely by the events
the framework emits. They are set up once when the server starts, called whenever a
subscribed event fires, and torn down when the server stops.

## Plugins vs event hooks

| | Event Hook | Plugin |
|---|---|---|
| Execution model | Called each time a subscribed event fires | Continuous async loop |
| Lifecycle | `on_setup`, `on_triggered` (N times), `on_teardown` | `on_started`, `on_running`, `on_stopped`, ... |
| Use case | Reacting to a discrete framework event | Periodic or long-running background work |

Use an event hook when your logic should fire in direct response to something the
framework emitted. Use a plugin when you need a persistent loop or scheduled work that
runs independently of individual events.

## How event hooks work

A event hook is a Python class that inherits from `BaseEventHook`. The set of events it
subscribes to is declared as a class-level `event_types` attribute. The framework calls
three hook methods:

```
on_setup()        called once when the hook is registered (server startup)
on_triggered()    called each time a subscribed event fires
on_teardown()     called once when the hook is unregistered (server shutdown)
```

`on_triggered()` receives an `Event` object carrying the event type, a human-readable
message, and any structured data associated with the event.

## Event object

Every call to `on_triggered()` receives an `Event`:

| Attribute | Type | Description |
|---|---|---|
| `event.event_type` | `EventType` | The `EventType` value that fired |
| `event.message` | `str` | Human-readable description of what happened |
| `event.data` | `dict` | Structured data payload (contents vary by event type) |

You can also call `event.to_json()` to get a plain dict with all three fields as strings.

## Project structure

Each event hook lives in its own directory under `consortium/components/event_hooks/`.
The directory must contain at minimum:

```
consortium/components/event_hooks/my_event_hook/
    manifest.json
    event_hook.py
```

`manifest.json` points the loader at the entry class and controls whether the hook is
loaded:

```json
{
    "entry_point": "event_hook:EventHook",
    "enabled": true
}
```

The entry point class must be named `EventHook` by convention.

## Real-world examples

`consortium/components/event_hooks/webhook_sender/` is the canonical reference
implementation. It demonstrates:

- Loading and validating a `config.json` in `on_setup`
- Dynamically adjusting `self.event_types` based on config at setup time
- Storing config in `self.environment` and reading it in `on_triggered`
- Making async HTTP requests inside `on_triggered` with retry logic
- Supporting multiple webhook platforms via a private helper method

Read `webhook_sender/event_hook.py` alongside this documentation for a concrete
working example.
