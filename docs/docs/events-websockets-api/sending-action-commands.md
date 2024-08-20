After making a websocket connection, the server will wait for the client to send
commands to it. The only time the server will send data to the client unprompted is
when a client is subscribed to an event, and that event fires on the server. All
messages sent over the websocket are sent as formatted strings of JSON data.

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

The message flow is simple. Take note however, that:

1. Events can come back to you at any moment in any order. You should be prepared to
handle this.
2. The first message received from the websocket _immediately after_ sending an action
command will always be some form of action command response. You do not have to worry
about scenarios in which a subscribed event is sent to you before the server returns a
response to your action command.
3. Each websocket connection is treated as a separate entity. This means that the same
client can open and close websockets to the events API independently where each
websocket is subscribed to different events.

## The Action Commands JSON Format
Action commands are pieces of structured JSON strings that are sent to the events API
over a websocket connection to interact with it. They follow this structure

```json title="Action command"
{
  "action": "ACTION_COMMAND_STRING",
  "events": ["EVENT_TYPE_1", "EVENT_TYPE_2", "EVENT_TYPE_3"]
}
```

!!! note

    The events field is required or not required depending on the type of action being
    performed. When it is not required, it **must be _entirely omitted_ from the JSON
    data**. Do not provide an empty list.


| Key      | Descripton                                                                                                                                  |
|----------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `action` | A string specifying the type of action to perform for the API. This field is **required**.                                                      |
| `events` | A list of strings specifying the events to perform the specified action on. This field is **optional** depending on the action being performed. |

The below are the types of action commands supported by the events API.

| Action Command            | Description                                                                        | Events field required? |
|---------------------------|------------------------------------------------------------------------------------|------------------------|
| `subscribe`               | Subscribe to events to be notified of for the current websocket.                   | Yes                    |
| `unsubscribe`             | Unsubscribe to events to be notified of for the current websocket.                 | Yes                    |
| `get_subscribed_events`   | Get the strings of all the events that the current websocket is subscribed to.     | No                     |
| `get_unsubscribed_events` | Get the strings of all the events that the current websocket is not subscribed to. | No                     |
| `get_all_events`          | Get the strings of all the available events that events API supports.              | No                     |


And here are all the supported events. The events when provided in the `events` field
list must be provided in uppercase, _ad verbatim_ to how they are formatted here.

| Event          | Description                      |
|----------------|----------------------------------|
| `START_SERVER` | Triggers when the server starts. |
| `STOP_SERVER`  | Triggers when the server stops.  |

!!! warning

    The supported events are still incomplete and may change in the future.

We will build on the script from the
[previous section](authentication.md#putting-it-all-together) to subscribe to events to
be notified of.

## Subscribing to events

## Responding to events
Due to the nature of the events systems in the framework, events will arrive
arbitrarily in any order over the websocket depending on when they fire. A system must
be created to resolve events to the correct event handlers.

There are two common ways to resolve events.

1. Creating separate websockets per event. Everytime you subscribe to a new event,
create a new websocket connection. This guarantees that all events received per
websocket will always be of the same event.
2. Creating an event handler dispatch system. Use a single websocket and continuously
read responses from it, depending on what is read, dispatch it to the correct function.

Option 1 is simpler but more resource intensive as more connections need to be opened,
option 2 is more complex due to the event handler resolution system but more resource
efficient.
