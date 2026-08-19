# Event Logger Hook

Appends framework events to a newline-delimited JSON file for offline analysis.

- Label: `event_logger_hook`
- Enabled by default: no

## What it does

On `on_setup` the hook loads `config.json` from its root directory and validates it with
Pydantic. A missing, malformed or invalid config raises out of setup, so the hook fails
to load rather than loading inert (see [Failure behaviour](#failure-behaviour) below).
It then narrows its subscriptions to `event_types` (the class declares every member of
`EventType`, so a config subset is applied by unsubscribing from the rest), resolves the
output path, creates the parent directories, and starts a single background writer task.

On `on_triggered` the event is serialised with `event.to_json()`, stamped with a UTC
timestamp, and put on an in-memory queue. Nothing touches the disk on this path, so
event dispatch is never blocked on a write. One record is one line:

```json
{"event_type": "AGENT_REGISTERED", "message": "Agent registered", "data": {}, "timestamp": "2026-08-20T09:15:04.512383+00:00"}
```

| Field | Source |
| ----- | ------ |
| `event_type` | `Event.event_type` as a string |
| `message` | `Event.message` |
| `data` | `Event.data`, verbatim |
| `timestamp` | Stamped when the event is enqueued, not when it is written |

The writer task takes one record off the queue, drains everything already queued behind
it, and appends the whole batch in one write on a worker thread. A burst of events
therefore costs one append rather than one per event, and because a single task owns the
writing, lines are never interleaved.

On `on_teardown` a stop sentinel is pushed onto the queue and the writer is awaited, so
everything queued ahead of the sentinel is flushed before the hook unloads.

## Failure behaviour

Configuration problems are fatal at load time; runtime problems are not. Nothing here
raises out of `on_triggered`:

| Situation | Behaviour |
| --------- | --------- |
| `config.json` missing | `on_setup` raises `FileNotFoundError`. The registry wraps it as `EventHookSetupError`, rolls back the declared subscriptions, and the hook does not load. |
| `config.json` malformed, invalid, or carrying an unknown key | `on_setup` raises `ValueError` with the validation error. Same outcome as above. |
| Output directory cannot be created | The `OSError` propagates out of `on_setup` and the hook does not load. |
| A write fails at runtime | Logged as an error naming the output file, that batch is dropped, and the writer keeps draining the queue. |
| The queue is full (only possible with `queue_max_size` set) | `on_triggered` waits for space, applying backpressure to event dispatch. |
| The server is killed rather than shut down | `on_teardown` never runs and queued-but-unwritten records are lost. |

Unknown config keys are rejected deliberately: a typo in a hand-edited config is a
startup failure rather than a silently ignored setting. If you would rather a bad config
degrade instead, catch it in `on_setup` and log a failure there, as the webhook sender
hook does.

## Configuration

`config.json` is committed, since it holds no credentials. Edit it in this directory:

```json
{
    "output_file": "events.jsonl",
    "event_types": null,
    "queue_max_size": null
}
```

- `output_file` (required): where records are appended. A relative path is resolved
  against this directory, so the default works regardless of the server's working
  directory. Missing parent directories are created; an existing file is appended to.
- `event_types` (default `null`): `null` records every event type. Supply a list of
  `consortium.framework.event_hooks.EventType` names (`AGENT_TASK_COMPLETED`,
  `LISTENER_STARTED`, `PAYLOAD_CREATED`, and so on) to narrow it.
- `queue_max_size` (default `null`): `null` leaves the queue unbounded, trading a memory
  ceiling for never blocking dispatch. Set an integer to cap it, accepting that
  `on_triggered` then waits when the writer falls behind.

Config is read once during setup, so restart the server or reload the hook after
editing.

## Usage

The hook ships disabled, since it appends to disk for every event it receives. Turn it
on in `manifest.json`:

```json
{
    "entry_point": "event_logger_hook:EventLoggerHook",
    "enabled": true
}
```

Restart the server and watch the file fill up:

```powershell
Get-Content events.jsonl -Wait -Tail 10
```

Starting the server is the easiest event to trigger. Each line is standalone JSON, so
`jq`, `pandas.read_json(..., lines=True)` and similar tools read the file directly.

## Notes

- Events are dispatched concurrently, so `on_triggered` can be re-entered before an
  earlier call returns. Line order is the order the puts complete, which under concurrent
  dispatch need not match `timestamp` order exactly. Sort by `timestamp` when order
  matters.
- The output file grows without bound and is not rotated or gitignored. Rotate or clean
  it externally, and keep it out of commits.
- Records contain event `data` verbatim, which for agent and listener events includes
  operational detail about your infrastructure. Treat the file as sensitive.
- The hook has no external dependencies, so it ships without a `pyproject.toml`.
- Narrowing is applied with `unsubscribe_from_event_type()`. The `event_types` class
  attribute is only the static declaration; `subscribed_event_types` is the read-only
  view of what the hook currently receives, and `subscribe_to_event_type()` /
  `unsubscribe_from_event_type()` are the only ways to change it.
