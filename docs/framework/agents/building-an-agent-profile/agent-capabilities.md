# Agent Capabilities

Capabilities are the commands an agent can execute. Each capability is a
`BaseAgentCapability` subclass (or a class returned by a factory) that handles one
command end-to-end: sending the task to the agent, awaiting its response, and returning
a result.

## The capability lifecycle

```
execute(task_message) called by the framework
  -> on_launch(task_message)    # mutate or abort before the message is sent
  -> framework transmits message to the agent
  -> on_execute()               # await and interpret the agent's response(s)
  -> returns Success, Failure, or None
```

## Writing a custom BaseAgentCapability

When a capability requires a multi-message exchange (file download, interactive shell,
streaming output), subclass `BaseAgentCapability` directly and override `on_launch`
and/or `on_execute`:

```python
import pathlib

from consortium.framework.agents import (
    BaseAgentCapability,
    Failure,
    Success,
    TaskLaunchMessageModel,
)
from consortium.framework.options import SingleValueOption


class DownloadCapability(BaseAgentCapability):
    name = "download"
    description = "Download a file from the agent to the server."
    authors = {"Your Name"}
    options = {
        SingleValueOption(
            name="source",
            description="Absolute path on the agent to download.",
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="destination",
            description="Local directory to save the file into.",
            required=False,
            value_type=str,
        ),
    }

    async def on_launch(
            self, task_message: TaskLaunchMessageModel
    ) -> TaskLaunchMessageModel:
        # Remove destination before sending -- it is a server-side concern only
        task_message.arguments.pop("destination", None)
        return task_message

    async def on_execute(self) -> Success | Failure | None:
        # First message: metadata header sent by the agent
        header = await self.recv_from_agent()
        if not header.success:
            return Failure(task_output_message=header)

        filename = pathlib.Path(header.data["path"]).name
        total_bytes = header.data.get("size", 0)
        received = 0
        chunks = []

        self.update_progress(
            message=f"Starting download of '{filename}'.",
            percent_complete=0,
        )

        # Subsequent messages: binary chunks until end-of-transfer
        while True:
            msg = await self.recv_from_agent()
            if not msg.success:
                return Failure(task_output_message=msg)

            msg_type = msg.data.get("type")
            if msg_type == "chunk":
                chunks.append(msg.payload.data)
                received += len(msg.payload.data)
                pct = round(received / total_bytes * 100, 1) if total_bytes else 0
                self.update_progress(
                    message=f"Downloading '{filename}': {received}/{total_bytes} bytes",
                    percent_complete=pct,
                )
            elif msg_type == "end_of_transfer":
                break
            else:
                return Failure(message=f"Unexpected message type: {msg_type}")

        self.log_artifact(message=f"Downloaded '{filename}'")
        return Success(message=f"Download of '{filename}' complete.")
```

## on_launch

`on_launch(task_message)` is called before the message is transmitted. Return the
(possibly modified) `TaskLaunchMessageModel` to proceed, or return `None` to abort the
launch without sending anything. Raising `AgentCapabilityLaunchError` also aborts and
surfaces as a `Failure`:

```python
from consortium.framework.signal_exceptions import AgentCapabilityLaunchError


async def on_launch(self, task_message):
    if not self._check_precondition():
        raise AgentCapabilityLaunchError("Precondition not met.")
    return task_message
```

Common uses: stripping server-side arguments before the agent sees them, mutating
arguments based on the agent's known state, or aborting a task that cannot proceed.

## on_execute

`on_execute()` is called after the initial message has been sent. Use the inherited
communication methods to exchange messages with the agent:

| Method                                           | Direction       | Notes                                                                |
|--------------------------------------------------|-----------------|----------------------------------------------------------------------|
| `await self.recv_from_agent(timeout=None)`       | Agent -> server | Blocks until the next `TaskOutputMessageModel` arrives for this task |
| `await self.send_to_agent(data={}, payload=b"")` | Server -> agent | Sends a `TaskInputMessageModel` for multi-turn exchanges             |
| `await self.send_and_recv_from_agent(data={})`   | Round trip      | Shorthand: send then immediately await reply                         |

`recv_from_agent` blocks until the agent submits a result with the matching `task_id`.
Call it once per expected message. For multi-message exchanges the agent must submit
multiple results with the same `task_id` until the exchange is complete.

## Emitting task events

Use these methods to record structured output into the task's event stream. They can be
called from `on_execute()` at any point:

| Method                                                  | When to use                                                                               |
|---------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `self.update_progress(percent_complete, message, data)` | Ephemeral progress update; overwrites the current status without adding a permanent event |
| `self.log_success(message, data)`                       | Log a SUCCESS event log entry visible in the task timeline                                |
| `self.log_info(message, data)`                          | Log an INFO event log entry                                                               |
| `self.log_failure(message, data)`                       | Log a FAILURE event log entry                                                             |
| `self.log_warning(message, data)`                       | Log a WARNING event log entry                                                             |
| `self.log_error(message, data)`                         | Log an ERROR event log entry                                                              |
| `self.log_artifact(message, data)`                      | Signal that the capability produced a collectible output (file, screenshot, etc.)         |

## TaskOutputMessageModel

The object returned by `recv_from_agent()`:

| Field     | Type              | Description                                         |
|-----------|-------------------|-----------------------------------------------------|
| `task_id` | `uuid.UUID`       | Must match the task ID sent to the agent            |
| `success` | `bool`            | Whether the agent considers the response successful |
| `message` | `str`             | Human-readable result description                   |
| `data`    | `dict`            | Structured result payload                           |
| `payload` | `Payload \| None` | Optional binary output                              |

`payload.data` returns the raw bytes synchronously. Use `await payload.load()` for
streamed payloads.

## Success and Failure

`on_execute()` must return `Success`, `Failure`, or `None`. Both accept either an
existing `task_output_message` to wrap, or `message` and `data` keyword arguments:

```python
return Success(message="Command completed.", data={"stdout": output})
return Failure(message="Agent returned non-zero exit code.", data={"exit_code": 1})
return Failure(task_output_message=header)   # wrap an existing message model
```

## What lives on self

| Attribute                      | Type                             | Description                                                            |
|--------------------------------|----------------------------------|------------------------------------------------------------------------|
| `self.name`                    | `str`                            | Capability name (class attribute; routes task dispatch)                |
| `self.description`             | `str`                            | Human-readable description                                             |
| `self.authors`                 | `set[str]`                       | Author identifiers                                                     |
| `self.requires_admin`          | `bool`                           | Whether elevated privileges are required                               |
| `self.supported_oses`          | `set[SupportedOS]`               | Platform restrictions                                                  |
| `self.is_atomic`               | `bool`                           | Whether this maps to a single MITRE ATT&CK step                        |
| `self.options`                 | `dict`                           | Name-keyed option definitions (converted from set at class definition) |
| `self.mitre_attack_techniques` | `list`                           | Resolved MITRE ATT&CK technique objects                                |
| `self.launch_message`          | `TaskLaunchMessageModel \| None` | The message sent on the most recent `execute()` call                   |
| `self.agent`                   | `Agent`                          | The agent this execution is running against                            |
| `self.task`                    | `AgentTask`                      | The task record tracking this execution                                |
| `self.services`                | namespace                        | All framework services                                                 |

`SupportedOS` is a `StrEnum` with values `WINDOWS`, `LINUX`, `MACOS`, `ANDROID`, `IOS`,
and `ANY`. The class attributes `SupportedOS.DESKTOP` and `SupportedOS.MOBILE` are
pre-built convenience sets:

```python
supported_oses = SupportedOS.DESKTOP                        # {WINDOWS, LINUX, MACOS}
supported_oses = SupportedOS.MOBILE                         # {ANDROID, IOS}
supported_oses = {SupportedOS.WINDOWS, SupportedOS.LINUX}   # explicit set
```
