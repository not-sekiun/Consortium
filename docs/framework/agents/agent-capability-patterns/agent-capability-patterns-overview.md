# Agent Capability Patterns Overview

## What these are

Every capability in this framework extends `BaseAgentCapability` and is driven by
one shared entry point, `execute()`:

1. `execute()` calls `on_launch(task_launch_message)`, giving the capability a
   chance to inspect or mutate the launch (or deny it by raising
   `AgentCapabilityLaunchError`).
2. It sends whatever `TaskLaunchMessage` `on_launch` returns to the agent.
3. It calls `on_execute()`, which awaits and processes the agent's response(s)
   and returns the task's outcome.

Each of the five classes documented here is a **template** that hardens one shape
of that `on_execute` loop into a reusable base class implementing `on_launch` and
`on_execute` itself (both `@final`) and exposing only the narrower hooks relevant
to that shape (e.g. `on_response`, `on_task_output`). You may
subclass one of these rather than `BaseAgentCapability` directly, and only
override the hooks it exposes.

They all share the same vocabulary:

- **`TaskLaunchMessage`**: sent once, by `execute()`, to start the exchange.
- **`TaskInputMessage`**: sent during the loop, for capabilities that talk more
  than once.
- **`TaskOutputMessage`**: received from the agent; converted to an outcome via
  `.to_outcome()`.
- **`Success` / `Failure`**: the terminal outcome of the task.
- **`Finish`**: a sentinel meaning "stop here, with no explicit
  `Success`/`Failure`."

## The patterns at a glance

| Capability | Outgoing | Incoming | Shape |
|---|---|---|---|
| [Request-Response](request-response-capability.md) | single | single | One launch, one response: a plain synchronous call. |
| [Outgoing Stream](outgoing-stream-capability.md) | stream | single (final only) | Many inputs sent, then one final response processed. |
| [Incoming Stream](incoming-stream-capability.md) | single (launch only) | stream | One launch, then many responses consumed. |
| [Bidirectional Stream](bidirectional-stream-capability.md) | stream | stream, concurrent | Full duplex; both directions run at once, with gRPC-style half-close termination. |
| [Lock-Step Stream](lock-step-stream-capability.md) | stream, turn-based | stream, turn-based | Alternating rounds: `Launch (Input Output)*`. |

- **[Request-Response Capability](request-response-capability.md)**: send one
  message, get one message back. No streaming on either side.
- **[Outgoing Stream Capability](outgoing-stream-capability.md)**: customizes
  only the outgoing side: send as many inputs as needed, then await a single
  final response.
- **[Incoming Stream Capability](incoming-stream-capability.md)**: customizes
  only the incoming side: after the launch, just keep consuming responses until
  one of them ends the exchange.
- **[Bidirectional Stream Capability](bidirectional-stream-capability.md)**: both
  sides run concurrently, like a full-duplex virtual TTY, with a half-close model
  for ending the exchange cleanly.
- **[Lock-Step Stream Capability](lock-step-stream-capability.md)**:
  turn-based rounds streamed in lock step, where each response feeds the
  construction of the next input, with a per-round receive timeout whose
  disposition is owned by `on_timeout`: by default it errors the task, but it can be
  overridden to wait again (a receive-retry that keeps the strict pairing intact, with
  `attempt`-based backoff), stop cleanly, or report an outcome. The framework never
  resends or advances the round for you.
