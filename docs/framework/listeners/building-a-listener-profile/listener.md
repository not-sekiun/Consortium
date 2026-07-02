# Listener

`BaseListener` is where the network server lives. It inherits from `ComponentLifeCycle`
and is responsible for implementing the agent-listener protocol: accepting registrations,
delivering tasks, and receiving results. All three obligations are fulfilled through
`self.connected_agents_service`.

## Protocol obligations

Every listener must fulfil three obligations via `self.connected_agents_service`. These
are the only operations the framework requires the listener to perform; everything else
(framing, authentication, transport encoding) is up to the implementation.

### 1. Agent registration

An agent connecting for the first time supplies identifying information. The listener
calls `register_agent` to create the agent's record in the framework:

```python
agent = self.connected_agents_service.register_agent(
    payload_id="<uuid of the payload this agent was generated from>",
    # OR: agent_type="my_type_name"   -- fallback when no payload_id is available
    endpoint=remote_address,
    remote_host_address=remote_address,
    user="DESKTOP\\alice",
    is_admin=False,
    os="Windows",
    version="10.0.26200",
    arch="x86_64",
    pid=4567,
    locale="en-US",
    local_host_address="192.168.1.50",
    hostname="DESKTOP-ABC",
)
# agent.agent_id is the UUID the framework assigned; send it back to the agent
```

Exactly one of `payload_id` or `agent_type` must be provided. `payload_id` is
preferred: it links the registered agent back to the generated payload and resolves the
agent type automatically. `agent_type` is a fallback for agents that self-identify by
type name. All other fields are optional system metadata that improve the agent's detail
view.

`register_agent` is synchronous. The `Agent` it returns has `agent.agent_id` (a
`uuid.UUID`) which must be sent back to the agent as its identity token.

### 2. Task delivery

When a registered agent polls for pending work:

```python
task_messages = await self.connected_agents_service.get_next_agent_task_messages_by_agent_id(
    agent_id=agent_id,
    count=None,    # None returns all pending tasks
    block=False,   # False returns immediately even if the queue is empty
)
```

This call also records an automatic check-in for the agent. Each returned object is a
`TaskLaunchMessageModel`:

| Field | Type | Description |
|---|---|---|
| `task_id` | `uuid.UUID` | Unique task identifier; the agent echoes this back in every result message |
| `command` | `str` | Capability name (matches `BaseAgentCapability.name`) |
| `arguments` | `dict` | Validated arguments from the operator |
| `data` | `dict` | Additional unvalidated data attached by the capability |
| `payload` | `Payload \| None` | Binary payload sent along with the task |

Serialize for transmission with `task_message.to_json()`. Binary payloads are excluded
from `to_json()` and require an out-of-band channel (multipart encoding, base64, etc.).

### 3. Result submission

When an agent submits a completed task result:

```python
await self.connected_agents_service.submit_result_by_agent_id(
    agent_id=agent_id,
    task_id=task_id,       # must match a running task for this agent
    success=True,
    message="Command executed successfully.",
    data={"stdout": "...", "stderr": ""},
    payload=raw_bytes,     # optional binary output
)
```

The service validates that the task ID corresponds to a running task on that agent,
records a check-in, and routes the result to the capability's `on_execute()` method via
an internal queue. For multi-message capabilities the agent submits multiple results
with the same `task_id`; each call to `submit_result_by_agent_id` unblocks one
`recv_from_agent()` call on the server side.

## Lifecycle hooks

### on_started: pre-flight checks

`on_started()` runs before `on_running()` is scheduled. Use it for one-time setup and
for failing fast if the listener cannot start. Raise `ListenerStartError` to abort
cleanly:

```python
import socket

from consortium.framework.exceptions import ListenerStartError
from consortium.framework.listeners import BaseListener


class Listener(BaseListener):

    async def on_started(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            probe.bind((local_host, local_port))
            probe.close()
        except OSError as exc:
            raise ListenerStartError(
                f"Cannot bind to {local_host}:{local_port}: {exc}",
            ) from None
        self.logger.info("TCP JSON Listener ready on {}:{}.", local_host, local_port)
```

`ListenerStartError` transitions the listener back to `INITIALIZED` and surfaces the
error to the caller. Do not raise bare exceptions; an unhandled exception in any hook
goes straight to `FATAL`.

### on_running: the network loop

`on_running()` is the main loop and runs as an asyncio Task. It must never block the
event loop. The canonical pattern is to start the server, store it on
`self.environment`, then `await self.stop_event.wait()` to keep the hook alive until
`stop()` is called:

```python
import asyncio
import json

from consortium.framework.listeners import BaseListener
from consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions import (
    AgentNotFoundError,
    AgentTypeResolutionError,
)


class Listener(BaseListener):

    async def on_running(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]

        async def handle_client(reader, writer):
            remote = writer.get_extra_info("peername", ("?", "?"))
            remote_addr = f"{remote[0]}:{remote[1]}"
            try:
                await self._handle_session(reader, writer, remote_addr)
            except Exception as exc:
                self.logger.warning("Session from {} aborted: {}", remote_addr, exc)
            finally:
                writer.close()

        server = await asyncio.start_server(handle_client, local_host, local_port)
        self.environment.server = server  # store for on_stopped / on_cancelled

        self.logger.info("Listening on {}:{}.", local_host, local_port)
        async with server:
            await self.stop_event.wait()  # block until stop() is called externally
```

The `handle_client` callback runs concurrently for each connection through the asyncio
event loop. All session state is local to the callback; do not store per-session state
as instance attributes. Use `self.environment` only for listener-wide runtime state.

The three protocol handlers dispatch from a per-session loop:

```python
    async def _handle_session(self, reader, writer, remote_addr):
        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                writer.write(b'{"error": "invalid json"}\n')
                await writer.drain()
                continue

            msg_type = message.get("type")
            if msg_type == "register":
                await self._handle_registration(message, writer, remote_addr)
            elif msg_type == "check_in":
                await self._handle_check_in(message, writer)
            elif msg_type == "result":
                await self._handle_result(message, writer)
            else:
                writer.write(b'{"error": "unknown message type"}\n')
                await writer.drain()

    async def _handle_registration(self, message, writer, remote_addr):
        try:
            agent = self.connected_agents_service.register_agent(
                payload_id=message.get("payload_id"),
                agent_type=message.get("agent_type"),
                endpoint=remote_addr,
                remote_host_address=remote_addr,
                user=message.get("user"),
                is_admin=message.get("is_admin"),
                os=message.get("os"),
                hostname=message.get("hostname"),
            )
        except AgentTypeResolutionError:
            writer.write(b'{"error": "unauthorized"}\n')
            await writer.drain()
            return
        writer.write((json.dumps({"agent_id": str(agent.agent_id)}) + "\n").encode())
        await writer.drain()

    async def _handle_check_in(self, message, writer):
        try:
            tasks = await self.connected_agents_service.get_next_agent_task_messages_by_agent_id(
                agent_id=message.get("agent_id", ""),
                count=None,
                block=False,
            )
        except AgentNotFoundError:
            writer.write(b'{"error": "unauthorized"}\n')
            await writer.drain()
            return
        writer.write((json.dumps([t.to_json() for t in tasks]) + "\n").encode())
        await writer.drain()

    async def _handle_result(self, message, writer):
        try:
            await self.connected_agents_service.submit_result_by_agent_id(
                agent_id=message.get("agent_id", ""),
                task_id=message["task_id"],
                success=message["success"],
                message=message.get("message", ""),
                data=message.get("data", {}),
            )
        except (AgentNotFoundError, KeyError):
            writer.write(b'{"error": "unauthorized"}\n')
            await writer.drain()
            return
        writer.write(b'{"ok": true}\n')
        await writer.drain()
```

### on_stopped and on_cancelled

`on_stopped()` runs when `stop()` is called. Use it to tear down resources started in
`on_running()`. `on_cancelled()` runs when the listener is cancelled externally; it
should release the same resources but may run before `on_running()` has finished
initialising, so guard attribute access with `hasattr`:

```python
    async def on_stopped(self) -> None:
        if hasattr(self.environment, "server"):
            self.environment.server.close()
            await self.environment.server.wait_closed()
        self.logger.info("TCP JSON Listener stopped.")

    async def on_cancelled(self) -> None:
        # stop() may have been called before on_running() stored the server
        if hasattr(self.environment, "server"):
            self.environment.server.close()
```

### Error handling

Raise `ListenerRuntimeError` from `on_running()` to signal a recoverable error:

```python
from consortium.framework.exceptions import ListenerRuntimeError

raise ListenerRuntimeError("Failed to process agent request: connection reset.")
```

This transitions the listener to `ERRORED` and calls `on_errored(error)`. Unhandled
exceptions go to `on_fatal(exc, fatal_context)` with a `ComponentLifeCycleFatalContext`
indicating which phase failed.

## What lives on self

| Attribute | Type | Description |
|---|---|---|
| `self.listener_id` | `uuid.UUID` | Unique identifier for this listener instance |
| `self.name` | `str` | Display name set at creation time |
| `self.description` | `str` | Description set at creation time |
| `self.endpoint` | `str` | Network endpoint derived by `resolve_listener_endpoint` |
| `self.listener_type` | `BaseListenerType` | Type descriptor (class attribute) |
| `self.parameters` | `dict` | Resolved option values from the template |
| `self.datetime_created` | `datetime` | Creation timestamp |
| `self.environment` | `SimpleNamespace` | Mutable runtime state; use this instead of instance attributes |
| `self.connected_agents_service` | `ConnectedAgentsService` | Agent lifecycle interface |
| `self.connected_agents` | `list[Agent]` | Property: agents currently connected to this listener |
| `self.stop_event` | `asyncio.Event` | Set when `stop()` is called from outside |
| `self.status` | `Status` | Lifecycle status; `.state` holds the current state string |
| `self.logger` | `loguru.Logger` | Listener-scoped logger |
| `self.services` | namespace | All framework services |
| `self.creating_listener_template` | `BaseListenerTemplate` | Template that created this instance (class attribute) |

Do not set runtime state as direct instance attributes. Use `self.environment` so that
`on_stopped` and `on_cancelled` can access it without risking `AttributeError` from
partially initialised state.

## ConnectedAgentsService methods

| Method | Sync/Async | Description |
|---|---|---|
| `register_agent(payload_id=..., agent_type=..., ...)` | sync | Create an agent record; supply either `payload_id` or `agent_type` |
| `get_next_agent_task_messages_by_agent_id(agent_id, count, block)` | async | Return pending tasks; auto check-in |
| `submit_result_by_agent_id(agent_id, task_id, success, message, data, payload)` | async | Forward a result to the capability; auto check-in |
| `deregister_agent_by_agent_id(agent_id)` | sync | Remove the agent from the framework entirely |
| `check_in_agent_by_agent_id(agent_id)` | sync | Manual check-in without task retrieval |
| `get_all_agents()` | sync | All agents connected to this listener |
| `get_agent_by_agent_id(agent_id)` | sync | Look up a single agent; validates it belongs to this listener |

`get_next_agent_task_messages_by_agent_id` and `submit_result_by_agent_id` are the only
async methods. All others are synchronous.
