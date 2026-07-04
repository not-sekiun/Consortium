# Event Hooks Overview

An event hook is a component that reacts to specific framework events. Unlike plugins,
which run continuously in the background, event hooks are driven entirely by the events
the framework emits. They are set up once when the server starts, called whenever a
subscribed event fires, and torn down when the server stops.

## Plugins vs event hooks

|                 | Event Hook                                          | Plugin                                        |
|-----------------|-----------------------------------------------------|-----------------------------------------------|
| Execution model | Called each time a subscribed event fires           | Continuous async loop                         |
| Lifecycle       | `on_setup`, `on_triggered` (N times), `on_teardown` | `on_started`, `on_running`, `on_stopped`, ... |
| Use case        | Reacting to a discrete framework event              | Periodic or long-running background work      |

Use an event hook when your logic should fire in direct response to something the
framework emitted. Use a plugin when you need a persistent loop or scheduled work that
runs independently of individual events.

## How event hooks work

A event hook is a Python class that inherits from `BaseEventHook`. The set of events it
subscribes to is declared as a class-level `event_types` attribute. The framework calls
three hook methods:

| Method           | Called                                               |
|------------------|------------------------------------------------------|
| `on_setup()`     | Once when the hook is registered (server startup)    |
| `on_triggered()` | Each time a subscribed event fires                   |
| `on_teardown()`  | Once when the hook is unregistered (server shutdown) |

`on_triggered()` receives an `Event` object carrying the event type, a human-readable
message, and any structured data associated with the event. See
[Event Hook Triggering](building-an-event-hook/event-hook-triggering.md) for the full
`Event` attribute
reference.

## Project structure

Each event hook lives in its own directory under `consortium/components/event_hooks/`,
containing at minimum a `manifest.json` and an `event_hook.py`. See
[Project Setup](building-an-event-hook/project-setup.md) for the full directory layout
and manifest format.

## Building an event hook

[Project Setup](building-an-event-hook/project-setup.md) walks through building a
complete event hook step by
step, from the initial directory layout through metadata, setup, triggering, teardown,
and code conventions, ending with a
[complete working example](building-an-event-hook/complete-event-hook-example.md) and
pointers to further
real-world reference implementations.
