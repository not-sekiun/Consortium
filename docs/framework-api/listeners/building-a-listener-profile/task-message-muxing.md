# Task Message Muxing

Each tasked capability has its own pair of queues. Its outbox carries messages from the
framework to the agent, beginning with a `TaskLaunchMessageModel`; its inbox carries
`TaskOutputMessageModel` values submitted by the agent. This isolation allows several
capabilities for one agent to make progress at the same time.

A listener reads task messages through `self.connected_agents_service`. Choose the reader
that matches the ordering your wire protocol needs.

| Reader | Use when | Ordering |
|--------|----------|----------|
| `get_next_task_message_sequential(agent_id, timeout)` | An agent processes one task stream at a time | Fully drains the earliest tasked outbox before reading the next |
| `get_next_task_message_any(agent_id, timeout)` | A polling or long-polling endpoint serves concurrent task streams | Returns the next available message across all capability outboxes |
| `get_next_task_message_by_task_id(agent_id, task_id, timeout)` | The agent is continuing a specific task stream | Returns only that task's messages, in order |

All three methods return a message or `None`. `timeout=None` waits indefinitely;
`timeout=0` returns immediately when no message is ready. A `None` from the task-specific
reader can also mean that task's outbox has reached end of stream and has been drained.

## Sequential task-by-task delivery

Sequential delivery is a canonical choice for a simple request-response protocol. It
fully serves the earliest task's message stream before starting the next task. Make one
long-poll read and send the returned message; the agent polls again after processing it:

```python
async def _handle_check_in(self, message, writer):
    try:
        task_message = await self.connected_agents_service.get_next_task_message_sequential(
            agent_id=message["agent_id"],
            timeout=30.0,
        )
    except AgentNotFoundError:
        writer.write(b'{"error": "unauthorized"}\n')
        await writer.drain()
        return

    response = task_message.to_json() if task_message is not None else None
    writer.write((json.dumps(response) + "\n").encode())
    await writer.drain()
```

The launch message is delivered first for each task. Retrieving it acknowledges the task
and transitions it to running, so the agent can then submit results for that `task_id`.
Later messages can be `TaskInputMessageModel` values for the same task. The listener must
preserve the `task_id` in its wire representation so the agent can associate every message
and result with the correct capability.

Messages within the current task outbox remain ordered. The reader moves to the next
earliest tasked outbox only after the current outbox reaches end of stream.

## Mux all capability outboxes

Muxed delivery is an equally canonical pattern for protocols that should serve whichever
capability has a message ready, without waiting for an earlier task to finish:

```python
task_message = await self.connected_agents_service.get_next_task_message_any(
    agent_id=agent_id,
    timeout=30.0,
)
```

Messages within each individual task outbox remain ordered. When multiple outboxes
already have a message ready, the service uses a stable task-start order to select one.

## Drain a task-specific stream

Streaming transports can keep a task stream open and drain that task's outbox directly:

```python
async for task_message in self.connected_agents_service.drain_task_messages_by_task_id(
    agent_id=agent_id,
    task_id=task_id,
):
    await send_message(task_message)
```

The generator ends only after the capability has finished and its buffered outbox messages
have been delivered. A capability can finish before the listener consumes every message;
the outbox remains available until the listener drains it. Do not read the same task from
multiple handlers unless your protocol deliberately coordinates those consumers.

## Route results back to the matching inbox

Every agent result must include the task ID from its launch message:

```python
await self.connected_agents_service.dispatch_task_output_message(
    agent_id=agent_id,
    task_id=result["task_id"],
    success=result["success"],
    message=result.get("message", ""),
    data=result.get("data", {}),
)
```

The service validates that the agent belongs to this listener, automatically records a
check-in, and puts the result into that task's inbox. Results for one capability never
block or get delivered to another capability's inbox. The listener-scoped service rejects
late results for a completed or deleted task, so handle that validation error in the wire
protocol.

Continue to [Listener Startup](listener-startup.md) to begin building the `Listener`
class.
