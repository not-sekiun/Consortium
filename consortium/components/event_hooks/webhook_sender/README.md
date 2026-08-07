# Webhook Sender Event Hook

Forwards server events to one or more webhooks. Discord, Slack and generic HTTP POST
targets are supported.

- Label: `consortium.event_hooks.webhook_sender`
- Enabled by default: yes

## What it does

On `on_setup` the hook loads `config.json` from its root directory, validates it against
a JSON schema, and adds every listed event name to `self.event_types`. Unknown event
names are logged as warnings and ignored; a missing, malformed or schema-invalid config
is logged as a failure and the hook subscribes only to its class level defaults
(`START_SERVER`, `STOP_SERVER`, `AGENT_REGISTERED`).

On `on_triggered` the event is serialised with `event.to_json()` and posted to every
configured webhook, with the payload shaped per platform:

| Platform  | Payload |
| --------- | ------- |
| `discord` | `{"embeds": [{"title": "Event: <event_type>", "description": <message>}]}` |
| `slack`   | `{"attachments": [{"title": <event_type>, "text": <message>}]}` |
| `generic` | `{"event_type": ..., "message": ..., "data": ...}` |

Only the generic payload carries the event's `data` field. Discord and Slack receive the
event type and message only.

Delivery is retried on connection errors and on any response status other than 200 or
204, up to `max_retries` attempts with `retry_delay_seconds` between them. Each failed
attempt is logged as a warning; once the attempts are exhausted the event is dropped.

## Configuration

Edit `config.json` in this directory:

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
editing.

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

- Webhook URLs in `config.json` are bearer credentials in plaintext. Do not commit real
  ones; the values currently in the file should be treated as compromised and rotated.
- Event messages are forwarded to third party services as-is, which for agent and
  listener events includes operational detail about your infrastructure.
