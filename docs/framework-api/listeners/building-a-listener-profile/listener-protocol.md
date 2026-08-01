# The Agent-Listener Protocol

Before writing the network server, it is worth pinning down exactly what that server must
do. A listener may speak any wire protocol you like (HTTP, raw TCP, DNS, anything), but
whatever the transport, it must fulfil three obligations against the framework through
`self.connected_agents_service`. Everything else (framing, authentication, encoding) is
entirely up to your implementation.

The three obligations are:

1. **Registration** - accept an agent's first check-in and create its record.
2. **Task delivery** - hand a registered agent its pending tasks.
3. **Result submission** - forward an agent's task results back into the framework.

The next three pages build the `Listener` class that carries these out. This page is the
contract; the code there is how the contract is met. Each `self.connected_agents_service`
method below reappears wrapped in a handler on the [Running Loop](listener-running-loop.md)
page.

## 1. Agent registration

An agent connecting for the first time supplies identifying information. The listener
calls `register_agent` to create the agent's record in the framework:

```python
agent = self.connected_agents_service.register_agent(
    payload_id="<uuid of the payload this agent was generated from>",
    # OR: agent_type="my_type_name"   -- fallback when no payload_id is available
    endpoint=remote_address,
    remote_ip=remote_address,
    user="DESKTOP\\alice",
    is_admin=False,
    os="Windows",
    version="10.0.26200",
    arch="x86_64",
    pid=4567,
    locale="en-US",
    local_ip="192.168.1.50",
    hostname="DESKTOP-ABC",
)
# agent.agent_id is the UUID the framework assigned; send it back to the agent
```

Exactly one of `payload_id` or `agent_type` must be provided. `payload_id` is preferred:
it links the registered agent back to the generated payload and resolves the agent type
automatically. `agent_type` is a fallback for agents that self-identify by type name. All
other fields are optional system metadata that improve the agent's detail view.

`register_agent` is synchronous. The `Agent` it returns has `agent.agent_id` (a
`uuid.UUID`) which must be sent back to the agent as its identity token.

## 2. Task delivery

When a registered agent asks for work, read one message from the agent's capability
outboxes. This minimal protocol serves complete task streams one at a time:

```python
task_message = await self.connected_agents_service.get_next_task_message_sequential(
    agent_id=agent_id,
    timeout=30.0,  # long-poll for up to 30 seconds; use 0 to poll immediately
)
```

This call drains the earliest tasked capability's outbox before moving to the next task.
It is a canonical protocol pattern when an agent processes one task stream at a time. A
call returns `None` when the timeout expires without a message. The agent should send another
work request after handling the message. Other protocols can instead mux all capability
outboxes or read a specific task stream; see [Task Message Muxing](task-message-muxing.md).

The first message for a task is a `TaskLaunchMessageModel`:

| Field       | Type              | Description                                                                |
|-------------|-------------------|----------------------------------------------------------------------------|
| `task_id`   | `uuid.UUID`       | Unique task identifier; the agent echoes this back in every result message |
| `command`   | `str`             | Capability name (matches `BaseAgentCapability.name`)                       |
| `arguments` | `dict`            | Validated arguments from the operator                                      |
| `data`      | `dict`            | Additional unvalidated data attached by the capability                     |
| `payload`   | `Payload \| None` | Binary payload sent along with the task                                    |

The message stream can also contain `TaskInputMessageModel` values for an already-running
task. Both message types provide `to_json()`. Binary payloads are excluded from
`to_json()` and require an out-of-band channel (multipart encoding, base64, etc.).

Each capability owns an inbox and an outbox. The outbox holds messages sent to the
agent, while the inbox receives that task's results. The framework keeps a task's outbox
available until its buffered messages are drained, even if the capability has already
finished. This means listeners can safely resume draining output after a transient
network failure.

For the complete reader choices and their ordering guarantees, see
[Task Message Muxing](task-message-muxing.md).

## 3. Result submission

When an agent submits a completed task result:

```python
await self.connected_agents_service.dispatch_task_output_message(
    agent_id=agent_id,
    task_id=task_id,  # must match a running task for this agent
    success=True,
    message="Command executed successfully.",
    data={"stdout": "...", "stderr": ""},
    payload=raw_bytes,  # optional binary output
)
```

The service validates that the task ID corresponds to a running task on that agent,
records a check-in, and routes the result into that task's capability-specific inbox. For
multi-message capabilities the agent submits multiple results with the same `task_id`;
each call unblocks one `recv_from_agent()` call on the server side. The listener-scoped
service rejects results for completed or deleted tasks, so translate that validation error
into the appropriate wire response.

Continue to [Task Message Muxing](task-message-muxing.md) for the delivery-reader
choices, then [Listener Startup](listener-startup.md) to begin building the `Listener`
class.
