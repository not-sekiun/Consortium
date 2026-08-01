# Event Hook Setup

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

## self.environment

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

## self.logger

`self.logger` is a loguru logger bound with the hook's name and ID. Use `{}` placeholder
syntax rather than f-strings:

```python
self.logger.info("Processing event: {}.", event.event_type)
self.logger.warning("Unexpected event type: {}.", event.event_type)
```

## Loading config files

If your hook needs external configuration (like `webhook_sender`), load it in
`on_setup()`. Use `self.root_directory` to locate sibling files:

```python
async def on_setup(self) -> None:
    config_path = self.root_directory / "config.json"
    with config_path.open("r") as f:
        self.environment.config = json.load(f)
```

See below for what to do if `config_path` does not exist.

## Signalling setup failures

Raise `EventHookSetupError` from `on_setup()` to signal that the event hook cannot be
set up. This aborts registration: the event hook is not loaded, `on_triggered()` is
never called for it, and the registry surfaces the failure as an `EventHookSetupError`
(from
`consortium.server.exceptions.consortium_exceptions.event_hooks_consortium_exceptions`)
carrying your `message` and any structured `detail` you provide.

```python
from consortium.framework.signal_exceptions.event_hooks_signal_exceptions import (
    EventHookSetupError,
)


async def on_setup(self) -> None:
    config_path = self.root_directory / "config.json"
    if not config_path.exists():
        raise EventHookSetupError(
            message=f"config.json not found at '{config_path}'.",
            detail={"config_path": str(config_path)},
        )
    with config_path.open("r") as f:
        self.environment.config = json.load(f)
```

Do not catch and log setup failures internally, and do not let a bare, unexpected
exception escape `on_setup()` unremarked. Either way the event hook still fails to
load: raising `EventHookSetupError` explicitly gives the caller a clean, structured
error instead of a hook that appears loaded but is silently missing state, or a raw
traceback with no framework context.

Continue to [Event Hook Triggering](event-hook-triggering.md) to react to events.
