# Building an Event Hook

This guide builds a complete event hook step by step. The hook we will write is an
**Agent Activity Tracker**: it subscribes to agent lifecycle events, counts each event
type as it fires, and writes a summary report to a JSON file when the server shuts down.

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

## Step 1: The minimum viable event hook

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

### event_types

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

## Step 2: on_setup

`on_setup()` is called once when the event hook is registered, before any events fire.
Use it to initialise state in `self.environment` and load any external configuration.

```python
async def on_setup(self) -> None:
    self.environment.counts = {
        EventType.AGENT_REGISTERED: 0,
        EventType.AGENT_CHECKED_IN: 0,
        EventType.AGENT_TASKED: 0,
        EventType.AGENT_TASK_COMPLETED: 0,
        EventType.AGENT_DEREGISTERED: 0,
    }
    self.logger.info("Agent Activity Tracker is ready.")
```

### self.environment

`self.environment` is a `types.SimpleNamespace` created fresh each time the hook is
instantiated. Use it to carry mutable state across `on_triggered()` calls:

```python
# Initialise in on_setup
self.environment.counts = {}
self.environment.last_agent_name = None

# Read and mutate in on_triggered
self.environment.counts[event.event_type] += 1
```

Do not store runtime state as direct instance attributes. Using `self.environment` keeps
state clearly separated from class-level configuration and from the framework-managed
attributes on `self`.

### self.logger

`self.logger` is a loguru logger bound with the hook's name and ID. Use `{}` placeholder
syntax rather than f-strings:

```python
self.logger.info("Processing event: {}.", event.event_type)
self.logger.warning("Unexpected event type: {}.", event.event_type)
```

### Loading config files

If your hook needs external configuration (like `webhook_sender`), load it in
`on_setup()`. Use `self.event_hook_project_folder` to locate sibling files:

```python
async def on_setup(self) -> None:
    config_path = self.event_hook_project_folder / "config.json"
    if not config_path.exists():
        self.logger.error("config.json not found at '{}'.", config_path)
        return
    with config_path.open("r") as f:
        self.environment.config = json.load(f)
```

Note that unlike plugins, event hooks have no `PluginStartError` equivalent. If
`on_setup()` encounters a missing config file, the idiomatic response is to log the
error and return early, leaving `self.environment` without the expected state. Guard
against that in `on_triggered()` with a check like
`if not hasattr(self.environment, "config"): return`.

## Step 3: on_triggered

`on_triggered()` is called each time one of the subscribed events fires. The `event`
argument carries all information about what occurred:

```python
async def on_triggered(self, event) -> None:
    if event.event_type in self.environment.counts:
        self.environment.counts[event.event_type] += 1

    self.logger.info("[{}] {}", event.event_type, event.message)
```

### The Event object

| Attribute | Type | Description |
|---|---|---|
| `event.event_type` | `EventType` | The event identifier that fired |
| `event.message` | `str` | Human-readable description of what happened |
| `event.data` | `dict` | Structured data payload (contents vary by event type) |

`event.to_json()` returns `{"event_type": str, "message": str, "data": dict}`.

### Branching on event type

When an event hook subscribes to multiple event types that need different handling,
branch on `event.event_type`:

```python
async def on_triggered(self, event) -> None:
    self._record_event(event)

    if event.event_type == EventType.AGENT_REGISTERED:
        self.logger.success("New agent connected: {}", event.message)
    elif event.event_type == EventType.AGENT_DEREGISTERED:
        self.logger.info("Agent disconnected: {}", event.message)
    elif event.event_type == EventType.AGENT_TASKED:
        self.logger.info("Task dispatched: {}", event.message)
    elif event.event_type == EventType.AGENT_TASK_COMPLETED:
        self.logger.success("Task completed: {}", event.message)
    else:
        self.logger.debug("[{}] {}", event.event_type, event.message)
```

### Async code in on_triggered

Because `on_triggered()` is an async coroutine you can freely `await` inside it:

```python
async def on_triggered(self, event) -> None:
    await self._post_to_external_api(event)
    await asyncio.sleep(0)  # yield control back to the event loop if needed
```

The framework awaits each call to `on_triggered()` sequentially for a given hook
instance, so concurrent calls to the same hook are not possible. That said,
`on_triggered()` should complete promptly. A slow implementation blocks subsequent
events for this hook from being delivered. For heavy work (network I/O, file writes),
consider `asyncio.create_task()` to offload work and return immediately:

```python
async def on_triggered(self, event) -> None:
    # Schedule the heavy work as a background task and return immediately
    asyncio.create_task(self._send_webhook(event))
```

Be careful when using `create_task()` from a hook: the task runs independently and any
exception it raises will not be caught by the hook's error handling. Wrap the body in a
try/except if the task can fail.

## Step 4: on_teardown

`on_teardown()` is called once when the server shuts down and the hook is being
unregistered. Use it to flush state to disk, close open connections, or perform any
final cleanup:

```python
import json

async def on_teardown(self) -> None:
    summary_path = self.event_hook_project_folder / "last_session_summary.json"
    summary = {
        str(event_type): count
        for event_type, count in self.environment.counts.items()
    }
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)
    self.logger.info("Session summary written to '{}'.", summary_path)
```

`self.event_hook_project_folder` is a `pathlib.Path` pointing to the directory that
contains your event hook's source files. Use it exactly like `self.plugin_project_folder`
in plugins.

## Step 5: Private helpers and conventions

### Private methods

The same conventions as plugins apply. Underscore-prefixed methods are private helpers
not intended to be called from outside the class:

```python
async def on_triggered(self, event) -> None:
    self._record_event(event)
    self.logger.info("[{}] {}", event.event_type, event.message)

def _record_event(self, event) -> None:
    # Private: updates internal counters, not part of the hook's interface
    if event.event_type in self.environment.counts:
        self.environment.counts[event.event_type] += 1
```

Static helpers that do not access instance state should use `@staticmethod`:

```python
@staticmethod
def _format_summary(counts: dict) -> str:
    return "\n".join(f"  {k}: {v}" for k, v in counts.items())
```

### Using services

`self.services` exposes every framework service as an attribute, identical to plugins:

```python
# Enrich event data with a live lookup
listeners = self.services.listeners_service.get_all_listeners()
active_listener_count = sum(
    1 for l in listeners if l.status.state == "RUNNING"
)
```

Service calls are synchronous and should be used in `on_triggered()` without awaiting.

### What lives on self

| Attribute | Type | Description |
|---|---|---|
| `self.event_hook_id` | `uuid.UUID` | Unique identifier for this hook instance |
| `self.name` | `str` | Display name from the class attribute |
| `self.label` | `str` | Stable label from the class attribute |
| `self.event_types` | `set[EventType]` | Events this hook subscribes to |
| `self.environment` | `SimpleNamespace` | Mutable runtime state namespace |
| `self.services` | `SimpleNamespace` | Framework services namespace |
| `self.logger` | `loguru.Logger` | Hook-scoped logger |
| `self.event_hook_project_folder` | `pathlib.Path` | Path to this hook's source directory |

## Complete event hook

```python
import json

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

    async def on_setup(self) -> None:
        self.environment.counts = {
            EventType.AGENT_REGISTERED: 0,
            EventType.AGENT_CHECKED_IN: 0,
            EventType.AGENT_TASKED: 0,
            EventType.AGENT_TASK_COMPLETED: 0,
            EventType.AGENT_DEREGISTERED: 0,
        }
        self.logger.info("Agent Activity Tracker is ready.")

    async def on_triggered(self, event) -> None:
        self._record_event(event)

        if event.event_type == EventType.AGENT_REGISTERED:
            self.logger.success("New agent connected: {}", event.message)
        elif event.event_type == EventType.AGENT_DEREGISTERED:
            self.logger.info("Agent disconnected: {}", event.message)
        elif event.event_type == EventType.AGENT_TASKED:
            self.logger.info("Task dispatched: {}", event.message)
        elif event.event_type == EventType.AGENT_TASK_COMPLETED:
            self.logger.success("Task completed: {}", event.message)
        else:
            self.logger.debug("[{}] {}", event.event_type, event.message)

    async def on_teardown(self) -> None:
        summary_path = self.event_hook_project_folder / "last_session_summary.json"
        summary = {
            str(event_type): count
            for event_type, count in self.environment.counts.items()
        }
        with summary_path.open("w") as f:
            json.dump(summary, f, indent=2)
        self.logger.info("Session summary written to '{}'.", summary_path)

    def _record_event(self, event) -> None:
        if event.event_type in self.environment.counts:
            self.environment.counts[event.event_type] += 1
```

## Further examples

`consortium/components/event_hooks/webhook_sender/event_hook.py` is the most complete
reference implementation available. Beyond the basic pattern above, it demonstrates:

- Validating config against a JSON schema in `on_setup` using `jsonschema`
- Dynamic `event_types` population at setup time from a config file
- Async HTTP requests with retry logic in a private helper
- Handling multiple webhook platform formats inside `on_triggered`
- The guard pattern: checking `self.environment.config` exists before using it in
  `on_triggered`, since `on_setup` may have returned early due to a missing config file
