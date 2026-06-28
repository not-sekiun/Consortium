All messages sent from the server over the websocket are identified by a `type` field.
There are two types: `"response"` (replies to action commands) and `"event"` (pushed
when a subscribed event fires).

## Response (`type: "response"`)

Sent in reply to every action command. Always check `success` before reading further.

### Success

```json title="Success response"
{
  "type": "response",
  "success": true,
  "message": "Successfully subscribed to the provided events.",
  "data": null
}
```

| Field     | Type             | Description                                                                                                                                         |
|-----------|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `type`    | `"response"`     | Always `"response"` for action command replies.                                                                                                     |
| `success` | `true`           | Indicates the command succeeded.                                                                                                                    |
| `message` | string           | Human-readable summary of the outcome.                                                                                                              |
| `data`    | array or `null`  | A list of event type strings for `get_all_events`, `get_subscribed_events`, and `get_unsubscribed_events`. `null` for all other action commands. |

### Error

```json title="Error response"
{
  "type": "response",
  "success": false,
  "errors": [
    {
      "code": "INVALID_EVENT_TYPE_ERROR",
      "message": "Failed to subscribe to event. The provided event type 'BAD_EVENT' does not exist.",
      "detail": {"event": "BAD_EVENT"}
    }
  ]
}
```

| Field     | Type         | Description                                                                 |
|-----------|--------------|-----------------------------------------------------------------------------|
| `type`    | `"response"` | Always `"response"` for action command replies.                             |
| `success` | `false`      | Indicates the command failed.                                               |
| `errors`  | array        | One or more error objects. Batch commands may return multiple entries.      |

Each error object:

| Field     | Type              | Description                                                                                                     |
|-----------|-------------------|-----------------------------------------------------------------------------------------------------------------|
| `code`    | string            | Machine-readable error code. See the [error codes table](sending-action-commands.md#error-codes).              |
| `message` | string            | Human-readable description of the error.                                                                        |
| `detail`  | object or `null`  | Additional context about the failure, e.g. `{"event": "BAD_EVENT"}` when an unrecognized event is provided.   |

## Event (`type: "event"`)

Pushed to the client whenever a subscribed event fires on the server. The `type` field
is always `"event"`. Fields beyond `type` depend on the specific event — refer to each
event's documentation.

```json title="Event message (envelope only)"
{
  "type": "event"
}
```

!!! warning
    Event payload fields are not yet finalized and will be documented per event type
    once stable.
