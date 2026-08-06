# Event Hook Triggering

`on_triggered()` is called each time one of the subscribed events fires. The `event`
argument carries all information about what occurred:

```python
async def on_triggered(self, event) -> None:
    if event.event_type in self.environment.counts:
        self.environment.counts[event.event_type] += 1

    self.logger.info("[{}] {}", event.event_type, event.message)
```

## The Event object

| Attribute          | Type        | Description                                           |
|--------------------|-------------|-------------------------------------------------------|
| `event.event_type` | `EventType` | The event identifier that fired                       |
| `event.message`    | `str`       | Human-readable description of what happened           |
| `event.data`       | `dict`      | Structured data payload (contents vary by event type) |

`event.to_json()` returns `{"event_type": str, "message": str, "data": dict}`.

## Branching on event type

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

## Async code in on_triggered

Because `on_triggered()` is an async coroutine you can freely `await` inside it:

```python
async def on_triggered(self, event) -> None:
    await self._post_to_external_api(event)
    await asyncio.sleep(0)  # yield control back to the event loop if needed
```

## Concurrency and re-entrancy

Every handler subscribed to an event runs concurrently, so a slow `on_triggered()` no
longer delays delivery to other hooks or to connected websocket clients. Routine network
I/O inside `on_triggered()` is fine and does not need to be offloaded just to keep the
event pipeline moving.

`on_triggered()` is also re-entrant. Each trigger is dispatched as an independent task,
so a second event can enter `on_triggered()` before an earlier call has returned. Two
consequences when writing a hook:

- Do not assume calls to your hook are serialised, and do not assume events arrive in
  the order they were triggered. No ordering is guaranteed between hooks or between
  triggers.
- State mutated across an `await` needs a lock. State read and written without an
  intervening `await` is safe, because the event loop cannot switch coroutines partway
  through a step.

```python
async def on_setup(self) -> None:
    self.environment.counts = {}
    self.environment.pending = 0
    self.environment.lock = asyncio.Lock()


async def on_triggered(self, event) -> None:
    # Safe: no `await` between the read and the write, so no other call can interleave.
    self.environment.counts[event.event_type] = (
        self.environment.counts.get(event.event_type, 0) + 1
    )

    # Needs the lock: the value is read, awaited across, then written. Without it a
    # second call can read the same value before this one writes it back.
    async with self.environment.lock:
        pending = self.environment.pending + 1
        await self._flush(pending)
        self.environment.pending = 0
```

## Offloading with create_task

Offloading is still useful for genuine fire-and-forget work that the framework should
not wait on at all, such as work that should outlive the trigger:

```python
async def on_triggered(self, event) -> None:
    # Schedule the work as a background task and return immediately
    asyncio.create_task(self._send_webhook(event))
```

Be careful when using `create_task()` from a hook: the task runs independently and any
exception it raises will not be caught by the events service, so it will not be
reported as an `EventHookTriggerError` (see below). Wrap the body in a try/except if the
task can fail, and raise `EventHookTriggerError` from within that try/except if you
still
want the failure reported through the framework.

Note also that a task created this way is not cancelled when the trigger is, so it can
outlive server shutdown. Keep a reference to it and cancel it in `on_teardown()` if that
matters for your hook.

## Signalling trigger failures

Raise `EventHookTriggerError` from `on_triggered()` to signal that handling this
particular event failed. The events service remaps it to the consortium-level
`EventHookTriggerError`, preserving your `message` and `detail`, and collects it
alongside any other handler failures for that event. It does not stop other hooks (or
other handlers) subscribed to the same event from running.

```python
from consortium.framework.signal_exceptions.event_hooks_signal_exceptions import (
    EventHookTriggerError,
)


async def on_triggered(self, event) -> None:
    try:
        await self._post_to_external_api(event)
    except Exception as exc:
        raise EventHookTriggerError(
            message=f"Failed to post event to external API: {exc}",
            detail={"event_type": str(event.event_type)},
        ) from exc
```

Do not catch and log a failure internally and swallow it, and do not let it escape as a
bare, unhandled exception. Both approaches used to be considered acceptable for event
hooks; now that `EventHookTriggerError` exists, raise it instead so failures are
reported through the same structured `code`/`message`/`detail` shape as every other
framework error.

Continue to [Event Hook Teardown](event-hook-teardown.md) to clean up on shutdown.
