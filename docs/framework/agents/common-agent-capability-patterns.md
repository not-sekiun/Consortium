# Common agent capability patterns

This page is a cookbook. If you are thinking "I have a pattern X that I want to implement, what does X look like?", find the matching pattern below, copy the stripped-down recipe, and grow it from there.

Every recipe is a plain `on_execute` written against `BaseAgentCapability`. There are no template base classes to inherit from: the loop is yours, and the framework provides the communication primitives (`send_to_agent`, `recv_from_agent`) plus `self.event_logger` for task events.

!!! info "The rule of thumb"
    If you can read your `on_execute` top to bottom and see the whole exchange, you are doing it right. Reach for a helper only when the plain loop gets genuinely hard to write correctly.

## How a capability runs

Before the patterns, the calling convention. The framework drives every capability the same way:

```mermaid
sequenceDiagram
    participant F as Framework
    participant C as Capability
    participant A as Agent
    F->>C: on_launch(task_launch_message)
    C-->>F: (possibly modified) launch message
    F->>A: send launch message
    F->>C: on_execute()
    C->>A: send_to_agent(...) as needed
    A->>C: recv_from_agent(...) as needed
    C-->>F: Success | Failure | None
```

1. `on_launch(task_launch_message)` runs first. Override it for pre-flight work: validate options, strip server-side arguments, enrich the message. Return the message to send, or raise `AgentCapabilityLaunchError` to deny the launch.
2. The framework sends the launch message to the agent.
3. `on_execute()` runs. This is where your pattern lives. Talk to the agent with `send_to_agent` and `recv_from_agent`, and report progress or task events through `self.event_logger`.
4. Return an outcome.

| Return value | Meaning                                                                                                               |
| --- |-----------------------------------------------------------------------------------------------------------------------|
| `Success` | The task succeeded: an explicit terminal event is recorded.                                                           |
| `Failure` | The task failed: an explicit terminal event is recorded.                                                              |
| `None` | The task completed normally. Use this when everything worth reporting already went out through `self.event_logger`. |
| raise | The task is errored. Uncaught exceptions, including `TimeoutError` from `recv_from_agent`, end up here.               |

!!! tip "Launch versus input messages"
    The launch message is a handshake: it carries the command and arguments and is sent exactly once, by the framework. Inside `on_execute` you only ever build `TaskInputMessageModel` instances (or let `send_to_agent(data=...)` build them for you), so it is impossible to send a launch twice.

### Timeouts

`recv_from_agent(timeout=...)` raises `TimeoutError` when nothing arrives in time. Handle it inline like any other exception:

```python
try:
    response = await self.recv_from_agent(timeout=30)
except TimeoutError:
    return Failure(message="Agent did not respond within 30 seconds")
```

When you want to wait several times with growing patience, keep the timeout schedule in
your capability and retry explicitly:

```python
for timeout in (5, 15, 60):
    try:
        response = await self.recv_from_agent(timeout=timeout)
        break
    except TimeoutError:
        self.event_logger.info(
            f"Agent quiet after {timeout}s, waiting longer",
        )
else:
    return Failure(message="Agent never responded")
```

!!! warning "Retrying a receive never resends"
    Waiting again after a timeout only re-waits on the inbox. Nothing goes back over the wire, so no duplicate message can reach the agent. If you want to resend, do it explicitly with `send_to_agent`, and make sure the agent side can handle the duplicate.

## Pattern 1: Request-response

One message out, one message back. This is the default behavior of `BaseAgentCapability`, so the minimal version needs no `on_execute` at all.

```mermaid
sequenceDiagram
    participant C as Capability
    participant A as Agent
    C->>A: launch
    A->>C: response
```

Use it when the agent does one unit of work and reports once: run a command, query a value, take a snapshot.

```python
class Whoami(BaseAgentCapability):
    name = "whoami"
    description = "Return the current user on the agent."

    async def on_execute(self) -> Success | Failure | None:
        response = await self.recv_from_agent(timeout=30)
        response.message = response.message.strip()
        return response.to_outcome()
```

!!! info "The one-liner"
    The inherited default is `return (await self.recv_from_agent()).to_outcome()`. Only override `on_execute` when you need a timeout or want to post-process the response, as above.

    `to_outcome()` converts the received `TaskOutputMessageModel` into `Success` or
    `Failure` according to its `success` field, preserving its message and data.

## Pattern 2: Incoming stream

One launch, many responses. The agent streams messages back until it signals the end; your loop consumes them and decides when the exchange is over.

```mermaid
sequenceDiagram
    participant C as Capability
    participant A as Agent
    C->>A: launch
    A->>C: header
    loop until terminal message
        A->>C: chunk / progress
    end
    A->>C: end of transfer
```

Use it when the agent produces output over time and you only listen: downloading a rendered file, tailing simulation progress, streaming log output.

```python
class DownloadFile(BaseAgentCapability):
    name = "download_file"
    description = "Download a single file from the agent."

    async def on_execute(self) -> Success | Failure | None:
        header = await self.recv_from_agent(timeout=30)
        if not header.success:
            return Failure(task_output_message=header)

        file_path = pathlib.Path(header.data["path"])
        file_size = header.data.get("size", 0)
        downloaded = 0

        while True:
            response = await self.recv_from_agent(timeout=60)
            if not response.success:
                return Failure(task_output_message=response)

            match response.data.get("type"):
                case "chunk":
                    downloaded += len(response.payload.data)
                    self.event_logger.update_progress(
                        message=f"Downloading {file_path.name}",
                        percent_complete=downloaded / file_size * 100 if file_size else 0,
                    )
                case "end_of_file":
                    self.event_logger.artifact(message=f"Downloaded '{file_path.name}'")
                    return Success(message=f"Downloaded '{file_path.name}'")
                case unknown:
                    return Failure(message=f"Unknown message type: {unknown}")
```

The shape to copy: consume the header before the loop, then `recv` at the top of the loop and `match` on the message type. Sequence lives in code order, state lives in locals, and every way out of the exchange is a visible `return`.

!!! tip "Ephemeral versus recorded events"
    `update_progress` overwrites the task status and is safe to call per chunk. The
    `success`, `info`, `warning`, `failure`, `error`, and `artifact` methods append to
    the task's event log, so save them for things worth keeping, like a finished
    artifact.

## Pattern 3: Outgoing stream

Many messages out, one final response. You stream input to the agent, stop, then wait for a single acknowledgement.

```mermaid
sequenceDiagram
    participant C as Capability
    participant A as Agent
    C->>A: launch
    loop for each chunk
        C->>A: chunk
    end
    C->>A: end of stream
    A->>C: final response
```

Use it when the agent consumes a stream and reports once at the end: uploading a file, feeding a dataset, submitting a batch of commands to run unattended.

```python
class UploadFile(BaseAgentCapability):
    name = "upload_file"
    description = "Upload a single file to the agent."

    async def on_execute(self) -> Success | Failure | None:
        source = pathlib.Path(self.task_launch_message.arguments["source"])
        chunk_size = 1_000_000

        with source.open("rb") as file:
            while chunk := file.read(chunk_size):
                await self.send_to_agent(
                    data={"type": "chunk"},
                    payload=chunk,
                )
        await self.send_to_agent(data={"type": "end_of_stream"})

        final = await self.recv_from_agent(timeout=60)
        return final.to_outcome()
```

"I am done sending" is just falling out of the loop. There is no sentinel to return and no half-close protocol to learn: send your terminal message, then receive.

!!! danger "Do not block the event loop"
    `file.read` above is fine for a recipe, but large reads on slow storage block the event loop. In real capabilities run blocking I/O through `asyncio.to_thread` or an async file library.

## Pattern 4: Lock-step stream

Strict turn taking: send one input, wait for its response, use that response to build the next input. Input and output stay paired one to one.

```mermaid
sequenceDiagram
    participant C as Capability
    participant A as Agent
    C->>A: launch
    A->>C: response 0
    loop one round at a time
        C->>A: input n (built from response n-1)
        A->>C: response n
    end
```

Use it when each step depends on the last: stepping a physics simulation and reading the state back, paging through results with a cursor, an interactive protocol where the agent's answer decides your next question.

```python
class StepSimulation(BaseAgentCapability):
    name = "step_simulation"
    description = "Step a physics simulation until it converges or hits the step cap."

    async def on_execute(self) -> Success | Failure | None:
        max_steps = self.task_launch_message.arguments.get("max_steps", 100)

        # Response to the launch: the initial simulation state.
        state = await self.recv_from_agent(timeout=30)
        if not state.success:
            return Failure(task_output_message=state)

        for step in range(max_steps):
            if state.data.get("converged"):
                return Success(message=f"Converged after {step} steps")

            # Build the next input from the previous response, then wait for
            # its paired reply before doing anything else.
            await self.send_to_agent(
                data={"action": "step", "dt": state.data["suggested_dt"]}
            )
            state = await self.recv_from_agent(timeout=30)
            if not state.success:
                return Failure(task_output_message=state)

            self.event_logger.update_progress(
                message=f"Step {step + 1}/{max_steps}",
                percent_complete=(step + 1) / max_steps * 100,
            )

        return Failure(message=f"Did not converge within {max_steps} steps")
```

!!! warning "Never advance a round on a timeout"
    Lock step only works while sends and receives stay aligned. If a round's response times out, either keep waiting for that same response or stop the exchange. Skipping ahead and sending the next input desynchronizes the pairing, and there is no clean way back.

## Pattern 5: Bidirectional stream

Both directions flow at once: you send inputs while the agent streams outputs, with
neither side waiting on the other. The application protocol must define its terminal
messages. A capability should return only after the receive side determines that the
exchange is complete; returning closes the framework's task-message queues.

```mermaid
sequenceDiagram
    participant C as Capability
    participant A as Agent
    C->>A: launch
    par sending
        C->>A: command
        C->>A: command
        C->>A: end of input
    and receiving
        A->>C: output
        A->>C: output
        A->>C: terminal output
    end
```

Use it when the two directions are genuinely independent: streaming control commands while output streams back, live steering of a long-running render.

Consortium does not provide a duplex helper. Implement this pattern only when the two
directions are truly independent, using an `asyncio.TaskGroup` and the existing
`send_to_agent()` and `recv_from_agent()` primitives. Ensure that leaving the capability
cancels and awaits the sender task, and report received progress through
`self.event_logger.update_progress()`.

```python
import asyncio


class LiveRender(BaseAgentCapability):
    name = "live_render"
    description = "Send render controls while streaming render progress."

    async def on_execute(self) -> Success | Failure | None:
        controls = self.task_launch_message.arguments["controls"]

        async def send_controls() -> None:
            for control in controls:
                await self.send_to_agent(data={"type": "control", "value": control})
            await self.send_to_agent(data={"type": "end_of_input"})

        async def receive_output() -> Success | Failure:
            while True:
                response = await self.recv_from_agent(timeout=60)
                if not response.success:
                    return Failure(task_output_message=response)

                match response.data.get("type"):
                    case "progress":
                        self.event_logger.update_progress(
                            message=response.message,
                            percent_complete=response.data.get("percent", 0),
                        )
                    case "complete":
                        return response.to_outcome()
                    case unknown:
                        return Failure(message=f"Unexpected message type: {unknown}")

        async with asyncio.TaskGroup() as task_group:
            sender = task_group.create_task(send_controls())
            receiver = task_group.create_task(receive_output())
            outcome = await receiver
            if not sender.done():
                sender.cancel()

        return outcome
```

The sender may finish before the agent's final output arrives. Conversely, a terminal
output can arrive before every control is sent; cancelling and awaiting the sender keeps
the capability from leaving a background task behind.

!!! tip "Reactive sending"
    An async generator cannot see incoming messages, which is fine for independent streams. If a received message must trigger a new send (for example the agent asks for a frame to be resent), bridge the two loops with an `asyncio.Queue`: the receive loop puts work on the queue, and the outgoing generator yields from it.

!!! info "Escape hatch"
    Use an `asyncio.TaskGroup` only when this concurrency is necessary. The basic
    communication primitives are always available.

## Choosing a pattern

| Pattern | Sends | Receives | Coupling | Typical use |
| --- | --- | --- | --- | --- |
| Request-response | 1 (launch) | 1 | none | Run a command, query a value |
| Incoming stream | 1 (launch) | many | none | Download, tail progress |
| Outgoing stream | many | 1 | none | Upload, feed a dataset |
| Lock-step stream | many | many | each input built from the previous response | Simulation stepping, cursor paging |
| Bidirectional stream | many | many | independent, protocol-defined termination | Live steering, command streaming |

When in doubt start with the simplest pattern that could work and let the loop grow. Moving from request-response to an incoming stream is adding a `while` loop, not changing base classes.
