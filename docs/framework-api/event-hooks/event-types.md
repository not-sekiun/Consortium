# Event Types

`EventType` is a `StrEnum` defined in `consortium/framework/event_hooks/event_type.py`.
Each value is a string identifier for a specific framework occurrence. Use these values
in the `event_types` class attribute of a `BaseEventHook` subclass to declare which
events the hook subscribes to.

Because `EventType` is a `StrEnum`, its values compare equal to their string
representations. A set literal of strings like `{"AGENT_REGISTERED", "STOP_SERVER"}`
works anywhere a `set[EventType]` is expected.

## Server events

| EventType      | Fires when                                                             |
|----------------|------------------------------------------------------------------------|
| `START_SERVER` | The server has finished starting up and is ready to accept connections |
| `STOP_SERVER`  | The server has received a shutdown signal and is beginning to stop     |

## Listener events

| EventType                  | Fires when                                                  |
|----------------------------|-------------------------------------------------------------|
| `LISTENER_CREATED`         | A new listener instance is created from a listener template |
| `LISTENER_ADDED`           | A listener is added to the framework registry               |
| `LISTENER_UPDATED`         | A listener's properties are modified                        |
| `LISTENER_REMOVED`         | A listener is removed from the framework registry           |
| `LISTENER_STARTED`         | A listener transitions to the RUNNING state                 |
| `LISTENER_STOPPED`         | A listener transitions to the STOPPED state                 |
| `LISTENER_CANCELLED`       | A listener's run is cancelled                               |
| `LISTENER_RUNTIME_ERRORED` | A listener raises a `ListenerRuntimeError` during execution |

## Agent generator events

| EventType                         | Fires when                                                 |
|-----------------------------------|------------------------------------------------------------|
| `AGENT_GENERATOR_CREATED`         | A new agent generator is created from an agent template    |
| `AGENT_GENERATOR_ADDED`           | An agent generator is added to the framework registry      |
| `AGENT_GENERATOR_UPDATED`         | An agent generator's properties are modified               |
| `AGENT_GENERATOR_REMOVED`         | An agent generator is removed from the registry            |
| `AGENT_GENERATOR_STARTED`         | An agent generator transitions to the RUNNING state        |
| `AGENT_GENERATOR_STOPPED`         | An agent generator transitions to the STOPPED state        |
| `AGENT_GENERATOR_CANCELLED`       | An agent generator's run is cancelled                      |
| `AGENT_GENERATOR_RUNTIME_ERRORED` | An agent generator raises a runtime error during execution |

## Agent events

| EventType              | Fires when                                                         |
|------------------------|--------------------------------------------------------------------|
| `AGENT_REGISTERED`     | An agent successfully checks in and is registered in the framework |
| `AGENT_CHECKED_IN`     | A registered agent submits a check-in (heartbeat or status update) |
| `AGENT_UPDATED`        | An agent's properties are modified                                 |
| `AGENT_DEREGISTERED`   | An agent is removed from the framework registry                    |
| `AGENT_DELETED`        | An agent is deleted from the framework registry                    |
| `AGENT_TASKED`         | A task is dispatched to an agent                                   |
| `AGENT_TASK_COMPLETED` | An agent submits the result of a completed task                    |

## User events

| EventType         | Fires when                                             |
|-------------------|--------------------------------------------------------|
| `USER_LOGGED_IN`  | A user successfully authenticates and begins a session |
| `USER_LOGGED_OUT` | A user's session ends                                  |

## Resource events

Payload, asset, and artifact events all follow the same CRUD pattern.

| EventType          | Fires when                            |
|--------------------|---------------------------------------|
| `PAYLOAD_CREATED`  | A new payload is created and stored   |
| `PAYLOAD_UPDATED`  | A payload's properties are modified   |
| `PAYLOAD_DELETED`  | A payload is deleted                  |
| `ASSET_CREATED`    | A new asset is created and stored     |
| `ASSET_UPDATED`    | An asset's properties are modified    |
| `ASSET_DELETED`    | An asset is deleted                   |
| `ARTIFACT_CREATED` | A new artifact is created and stored  |
| `ARTIFACT_UPDATED` | An artifact's properties are modified |
| `ARTIFACT_DELETED` | An artifact is deleted                |

## Usage examples

Subscribe to a single event:

```python
from consortium.framework.event_hooks import BaseEventHook, EventType

class EventHook(BaseEventHook):
    event_types = {EventType.AGENT_REGISTERED}
```

Subscribe to all agent lifecycle events:

```python
event_types = {
    EventType.AGENT_REGISTERED,
    EventType.AGENT_CHECKED_IN,
    EventType.AGENT_UPDATED,
    EventType.AGENT_DEREGISTERED,
    EventType.AGENT_TASKED,
    EventType.AGENT_TASK_COMPLETED,
}
```

Subscribe to server lifecycle events only:

```python
event_types = {EventType.START_SERVER, EventType.STOP_SERVER}
```

Subscribe to all resource creation events:

```python
event_types = {
    EventType.PAYLOAD_CREATED,
    EventType.ASSET_CREATED,
    EventType.ARTIFACT_CREATED,
}
```

Dynamic subscription from a config file (as used by `webhook_sender`):

```python
async def on_setup(self) -> None:
    for event_name in self.environment.config["events"]:
        if event_name in EventType:
            self.event_types.add(event_name)
        else:
            self.logger.warning("'{}' is not a valid EventType.", event_name)
```
