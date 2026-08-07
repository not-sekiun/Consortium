# Webhook Sender Event Hook

Forwards server events to one or more webhooks. Discord, Slack and generic HTTP POST
targets are supported.

- Label: `consortium.event_hooks.webhook_sender`
- Enabled by default: yes

## What it does

On `on_setup` the hook loads `config.json` from its root directory, validates it against
a JSON schema, and subscribes to every listed event name. Unknown event names are logged
as warnings and ignored; a missing, malformed or schema-invalid config is logged as a
failure and leaves the hook loaded but inert (see
[Failure behaviour](#failure-behaviour) below).

On `on_triggered` the event is serialised with `event.to_json()` and posted to every
configured webhook, with the payload shaped per platform:

| Platform  | Payload |
| --------- | ------- |
| `discord` | `{"embeds": [{"title": "Event: <event_type>", "description": <message>}]}` |
| `slack`   | `{"attachments": [{"title": <event_type>, "text": <message>}]}` |
| `generic` | `{"event_type": ..., "message": ..., "data": ...}` |

Only the generic payload carries the event's `data` field. Discord and Slack receive the
event type and message only.

Delivery is retried on connection errors, timeouts, and any response status other than
200 or 204, up to `max_retries` attempts with `retry_delay_seconds` between them (a
configured value of 0 still makes one attempt). Each failed attempt is logged as a
warning, and exhausting them logs a failure naming the dropped event's destination.

## Failure behaviour

The hook is designed to degrade rather than interrupt the server. Nothing here raises
out of `on_triggered`:

| Situation | Behaviour |
| --------- | --------- |
| `config.json` missing, malformed, or schema-invalid | `on_setup` logs a failure and the hook loads inert. The first event logs one warning explaining it is not forwarding, then stays quiet. |
| `webhooks` set to `[]` | Setup warns once; events are received and discarded. |
| An event name is not a valid `EventType` | Warns and skips that name; the rest of the config still applies. |
| A webhook is unreachable, times out, or returns an error status | Retried, then logged as a failure and dropped. |
| One webhook fails unexpectedly | Logged, and the remaining webhooks still receive the event. |

Because the hook stays loaded when its config is bad, a misconfiguration shows up as
event log entries rather than a startup error. Check the hook's event log if events stop
arriving. If you would rather the hook refuse to load at all, raise `EventHookSetupError`
from `on_setup` instead of returning.

## Configuration

`config.json` holds live webhook credentials and is gitignored. It is not shipped with
the repository, so create it from the committed template:

```bash
cp config.example.json config.json
```

Then edit `config.json` in this directory:

```json
{
    "events": [
        "STOP_SERVER",
        "START_SERVER",
        "AGENT_REGISTERED"
    ],
    "webhooks": [
        {
            "platform": "discord",
            "url": "https://discord.com/api/webhooks/<id>/<token>"
        },
        {
            "platform": "generic",
            "url": "https://example.internal/consortium-events"
        }
    ],
    "max_retries": 3,
    "retry_delay_seconds": 5
}
```

- `events`: event type names to subscribe to. Valid values are the members of
  `consortium.framework.event_hooks.EventType` (`AGENT_TASK_COMPLETED`,
  `LISTENER_STARTED`, `PAYLOAD_CREATED`, and so on).
- `webhooks`: one entry per destination. `platform` must be `discord`, `slack` or
  `generic`.
- `max_retries` (default 3) and `retry_delay_seconds` (default 5) apply to every
  webhook.

Config is read once during setup, so restart the server or reload the hook after
editing. Keep `config.example.json` in sync when the schema changes, but never put real
URLs in it.

## Usage

Enable or disable it in `manifest.json`:

```json
{
    "entry_point": "event_hook:EventHook",
    "enabled": true
}
```

Point the URLs at your own webhooks and restart the server. Triggering any subscribed
event (starting the server is the easiest) should produce a message at each destination.

## Notes

- Webhook URLs are bearer credentials in plaintext: anyone holding one can post to the
  channel. `config.json` is gitignored for that reason, so never commit it or paste real
  URLs into `config.example.json`.
- Events are dispatched concurrently to all handlers, so `on_triggered` can be re-entered
  before an earlier call returns. Each call opens its own `aiohttp.ClientSession`, and
  no ordering between forwarded events is guaranteed.
- Subscriptions from `events` are applied with `subscribe_to_event_type()`, which works
  at any point in the hook's lifecycle. The `event_types` class attribute is only the
  static declaration; `subscribed_event_types` is the read-only view of what the hook
  currently receives, and `subscribe_to_event_type()` /
  `unsubscribe_from_event_type()` are the only ways to change it.
- Event messages are forwarded to third party services as-is, which for agent and
  listener events includes operational detail about your infrastructure.
