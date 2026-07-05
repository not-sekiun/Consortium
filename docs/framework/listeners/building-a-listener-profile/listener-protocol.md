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

Exactly one of `payload_id` or `agent_type` must be provided. `payload_id` is preferred:
it links the registered agent back to the generated payload and resolves the agent type
automatically. `agent_type` is a fallback for agents that self-identify by type name. All
other fields are optional system metadata that improve the agent's detail view.

`register_agent` is synchronous. The `Agent` it returns has `agent.agent_id` (a
`uuid.UUID`) which must be sent back to the agent as its identity token.

## 2. Task delivery

When a registered agent polls for pending work:

```python
task_messages = await self.connected_agents_service.get_next_agent_task_messages_by_agent_id(
    agent_id=agent_id,
    count=None,  # None returns all pending tasks
    block=False,  # False returns immediately even if the queue is empty
)
```

This call also records an automatic check-in for the agent. Each returned object is a
`TaskLaunchMessageModel`:

| Field       | Type              | Description                                                                |
|-------------|-------------------|----------------------------------------------------------------------------|
| `task_id`   | `uuid.UUID`       | Unique task identifier; the agent echoes this back in every result message |
| `command`   | `str`             | Capability name (matches `BaseAgentCapability.name`)                       |
| `arguments` | `dict`            | Validated arguments from the operator                                      |
| `data`      | `dict`            | Additional unvalidated data attached by the capability                     |
| `payload`   | `Payload \| None` | Binary payload sent along with the task                                    |

Serialize for transmission with `task_message.to_json()`. Binary payloads are excluded
from `to_json()` and require an out-of-band channel (multipart encoding, base64, etc.).

## 3. Result submission

When an agent submits a completed task result:

```python
await self.connected_agents_service.submit_result_by_agent_id(
    agent_id=agent_id,
    task_id=task_id,  # must match a running task for this agent
    success=True,
    message="Command executed successfully.",
    data={"stdout": "...", "stderr": ""},
    payload=raw_bytes,  # optional binary output
)
```

The service validates that the task ID corresponds to a running task on that agent,
records a check-in, and routes the result to the capability's `on_execute()` method via
an internal queue. For multi-message capabilities the agent submits multiple results with
the same `task_id`; each call to `submit_result_by_agent_id` unblocks one
`recv_from_agent()` call on the server side.

Continue to [Listener Startup](listener-startup.md) to begin building the `Listener`
class.
