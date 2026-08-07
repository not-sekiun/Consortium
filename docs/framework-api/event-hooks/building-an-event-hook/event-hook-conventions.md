# Event Hook Conventions

## Private methods

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

## Using services

`self.services` exposes every framework service as an attribute, identical to plugins:

```python
# Enrich event data with a live lookup
listeners = self.services.listeners_service.get_all_listeners()
active_listener_count = sum(
    1 for l in listeners if l.status.state == "RUNNING"
)
```

Service calls are synchronous and should be used in `on_triggered()` without awaiting.

## What lives on self

| Attribute                     | Type                   | Description                                  |
|-------------------------------|------------------------|----------------------------------------------|
| `self.event_hook_id`          | `uuid.UUID`            | Unique identifier for this hook instance     |
| `self.name`                   | `str`                  | Display name from the class attribute        |
| `self.label`                  | `str`                  | Stable label from the class attribute        |
| `self.event_types`            | `frozenset[EventType]` | Events declared in the class body            |
| `self.subscribed_event_types` | `frozenset[EventType]` | Events subscribed to right now, read-only    |
| `self.environment`            | `SimpleNamespace`      | Mutable runtime state namespace              |
| `self.services`               | `SimpleNamespace`      | Framework services namespace                 |
| `self.logger`                 | `loguru.Logger`        | Hook-scoped logger                           |
| `self.root_directory`         | `pathlib.Path`         | Path to this hook's source directory         |

See the [Complete Event Hook Example](complete-event-hook-example.md) for all of these
concepts combined into one event hook.
