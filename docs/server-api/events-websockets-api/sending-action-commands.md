After connecting, the server waits for the client to send action commands. The server
only pushes data unprompted when a subscribed event fires. All messages over the
websocket are JSON strings.

## Message Flow

``` mermaid
sequenceDiagram
    participant C as Client
    participant WS as Websocket Server
    participant E as Events Service
    C->>+WS: Subscription action command (Subscribe to event A)
    WS-->>-C: Action command response
    E-->>WS: Event A occurs
    WS-->>C: Event A JSON data sent
    E-->>WS: Event A occurs
    C->>+WS: Subscription action command (Subscribe to event B)
    WS-->>-C: Action command response
    E-->>WS: Event B occurs
    WS-->>C: Event B JSON data sent
    WS-->>C: Event A JSON data sent
```

Key behaviors:

1. Events can arrive at any time in any order. Build your client to handle this.
2. The first message after sending an action command is always the response to that
   command. A subscribed event will never arrive before its subscription response.
3. Each websocket connection is independent. The same client can open multiple
   connections, each with its own set of subscriptions.
4. When a connection closes, all its subscriptions are automatically cleaned up.

## Action Command Format

```json title="Action command"
{
  "action": "ACTION_COMMAND_STRING",
  "events": ["EVENT_TYPE_1", "EVENT_TYPE_2"]
}
```

| Key      | Description                                                                                         |
|----------|-----------------------------------------------------------------------------------------------------|
| `action` | The action to perform. **Required**.                                                                |
| `events` | List of event type strings. Required for `subscribe`/`unsubscribe`, must be omitted for all others. |

!!! note
    When `events` is not required, **omit the field entirely** — do not pass an empty list.

| Action                    | Description                                          | `events` required? |
|---------------------------|------------------------------------------------------|--------------------|
| `subscribe`               | Subscribe this connection to one or more events.     | Yes                |
| `unsubscribe`             | Unsubscribe this connection from one or more events. | Yes                |
| `get_subscribed_events`   | Get all events this connection is subscribed to.     | No                 |
| `get_unsubscribed_events` | Get all events this connection is not subscribed to. | No                 |
| `get_all_events`          | Get all events the API supports.                     | No                 |

## Server Responses

Every action command receives exactly one response.
See [Server Messages](server-messages.md)
for the full schema. Check the `success` field to determine whether the command
succeeded.

**Success**

```json title="Success response"
{
  "type": "response",
  "success": true,
  "message": "Successfully subscribed to the provided events.",
  "data": null
}
```

**Error**

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

`errors` may contain multiple objects if a batch command fails on more than one item.

## Error Codes

| Code                                | When it occurs                                                   |
|-------------------------------------|------------------------------------------------------------------|
| `INVALID_MESSAGE_FORMAT_ERROR`      | The action command JSON is malformed or missing required fields. |
| `INVALID_EVENT_TYPE_ERROR`          | An event string does not match any known event type.             |
| `ALREADY_SUBSCRIBED_TO_EVENT_ERROR` | `subscribe` was called for an event already subscribed to.       |
| `NOT_SUBSCRIBED_TO_EVENT_ERROR`     | `unsubscribe` was called for an event not subscribed to.         |

!!! warning
    `subscribe` and `unsubscribe` validate **all** events in the list before applying
    any changes. If any event fails validation the entire command is rejected, no
    subscriptions are changed.

## Available Events

Event strings must be provided in uppercase exactly as shown.

| Event          | Description                      |
|----------------|----------------------------------|
| `START_SERVER` | Triggers when the server starts. |
| `STOP_SERVER`  | Triggers when the server stops.  |

!!! warning
    The events list is not finalized and will change.

## Subscribing to Events

Building on the script from [authentication](authentication.md#putting-it-all-together):

```py title="subscribe_to_events.py"
import asyncio
import json

import requests
import websockets

USERNAME = "admin"
PASSWORD = "admin"
AUTHORIZATION_URL = "http://localhost:9999/api/login"
EVENTS_API_URL = "ws://localhost:9999/api/ws/events"


def get_jwt(username: str, password: str, authorization_url: str) -> str:
    response = requests.post(
        authorization_url, data={"username": username, "password": password}
    )
    return response.json()["access_token"]


async def main() -> None:
    jwt = get_jwt(USERNAME, PASSWORD, AUTHORIZATION_URL)

    async with websockets.connect(
        EVENTS_API_URL, extra_headers={"Authorization": f"Bearer {jwt}"}
    ) as ws:
        await ws.send(json.dumps({
            "action": "subscribe",
            "events": ["START_SERVER", "STOP_SERVER"],
        }))
        response = json.loads(await ws.recv())

        if not response["success"]:
            for error in response["errors"]:
                print(f"Error: {error['code']} — {error['message']}")
            return

        print("Subscribed. Waiting for events...")
        async for raw_message in ws:
            message = json.loads(raw_message)
            if message["type"] == "event":
                print(f"Event received: {message}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Unsubscribing from Events

```py title="unsubscribe_example.py"
await ws.send(json.dumps({
    "action": "unsubscribe",
    "events": ["START_SERVER"],
}))
response = json.loads(await ws.recv())

if response["success"]:
    print("Unsubscribed successfully.")
else:
    for error in response["errors"]:
        print(f"Error: {error['code']} - {error['message']}")
```

## Querying Subscriptions

```py title="query_subscriptions.py"
# All events the API supports
await ws.send(json.dumps({"action": "get_all_events"}))
all_events = json.loads(await ws.recv())["data"]
print("All events:", all_events)  # e.g. ["START_SERVER", "STOP_SERVER"]

# Events this connection is subscribed to
await ws.send(json.dumps({"action": "get_subscribed_events"}))
subscribed = json.loads(await ws.recv())["data"]
print("Subscribed:", subscribed)

# Events this connection is not subscribed to
await ws.send(json.dumps({"action": "get_unsubscribed_events"}))
not_subscribed = json.loads(await ws.recv())["data"]
print("Not subscribed:", not_subscribed)
```

## Responding to Events

Events arrive on the same websocket as action command responses, so your receive loop
must distinguish between them using the `type` field (`"event"` vs `"response"`). There
are two common approaches.

### Approach 1: One websocket per event type

Open a separate connection for each event. Every message on that connection is
guaranteed to be the subscribed event — no routing logic needed.

```py title="one_ws_per_event.py"
import asyncio
import json

import requests
import websockets

USERNAME = "admin"
PASSWORD = "admin"
AUTHORIZATION_URL = "http://localhost:9999/api/login"
EVENTS_API_URL = "ws://localhost:9999/api/ws/events"


def get_jwt(username: str, password: str, authorization_url: str) -> str:
    return requests.post(
        authorization_url, data={"username": username, "password": password}
    ).json()["access_token"]


async def listen_for_event(jwt: str, event_type: str) -> None:
    async with websockets.connect(
        EVENTS_API_URL, extra_headers={"Authorization": f"Bearer {jwt}"}
    ) as ws:
        await ws.send(json.dumps({"action": "subscribe", "events": [event_type]}))
        await ws.recv()  # discard subscription response
        async for raw_message in ws:
            message = json.loads(raw_message)
            if message["type"] == "event":
                print(f"[{event_type}] {message}")


async def main() -> None:
    jwt = get_jwt(USERNAME, PASSWORD, AUTHORIZATION_URL)
    await asyncio.gather(
        listen_for_event(jwt, "START_SERVER"),
        listen_for_event(jwt, "STOP_SERVER"),
    )


if __name__ == "__main__":
    asyncio.run(main())
```

### Approach 2: Single websocket with a dispatcher

Use one connection and route incoming events to handlers by event type. More efficient
when subscribing to many events.

```py title="event_dispatcher.py"
import asyncio
import json
from collections.abc import Callable

import requests
import websockets

USERNAME = "admin"
PASSWORD = "admin"
AUTHORIZATION_URL = "http://localhost:9999/api/login"
EVENTS_API_URL = "ws://localhost:9999/api/ws/events"

EventHandler = Callable[[dict], None]


def get_jwt(username: str, password: str, authorization_url: str) -> str:
    return requests.post(
        authorization_url, data={"username": username, "password": password}
    ).json()["access_token"]


def on_start_server(event: dict) -> None:
    print("Server started:", event)


def on_stop_server(event: dict) -> None:
    print("Server stopped:", event)


async def listen(jwt: str, handlers: dict[str, EventHandler]) -> None:
    async with websockets.connect(
        EVENTS_API_URL, extra_headers={"Authorization": f"Bearer {jwt}"}
    ) as ws:
        await ws.send(json.dumps({
            "action": "subscribe",
            "events": list(handlers.keys()),
        }))
        await ws.recv()  # discard subscription response

        async for raw_message in ws:
            message = json.loads(raw_message)
            if message["type"] != "event":
                continue
            # The field that identifies the event type within the payload depends on
            # the event. Refer to the specific event's documentation.
            event_type = message.get("event_type")
            handler = handlers.get(event_type)
            if handler:
                handler(message)


async def main() -> None:
    jwt = get_jwt(USERNAME, PASSWORD, AUTHORIZATION_URL)
    await listen(jwt, {
        "START_SERVER": on_start_server,
        "STOP_SERVER": on_stop_server,
    })


if __name__ == "__main__":
    asyncio.run(main())
```

Approach 1 is simpler and appropriate for a small number of events. Approach 2 scales
better when subscribing to many events or when the overhead of multiple connections
matters.
