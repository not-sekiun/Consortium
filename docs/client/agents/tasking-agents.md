# Tasking Agents

Once a payload has been delivered and executed on a target, the agent connects back
through
its listener and checks in. From that point you manage and task it from the client. Two
interpreters are involved:

- The **Agents** interpreter (prompt `Consortium (Agents)`) lists all agents and inspects
  their tasks.
- The **Interact Agent** interpreter (prompt `Consortium (Agents: <name>)`) scopes you
  to a single agent so you can task it through its capabilities.

Switch into the Agents interpreter from any connected interpreter with the `agents`
command.

## The agents interpreter

On entry, the Agents interpreter lists all agents. It subscribes to `AGENT_REGISTERED`
and
`AGENT_TASKED` events, so new check ins are announced live and tab completion updates
automatically.

| Command               | Description                                  |
|-----------------------|----------------------------------------------|
| `list`                | List all agents                              |
| `info <agent_id>`     | Show details of an agent                     |
| `interact <agent_id>` | Enter the agent's context to task it         |
| `task`                | Manage agent tasks (see below)               |
| `rename <agent_id> <name>`               | Rename an agent                              |
| `describe <agent_id> <description>`       | Attach a description to an agent             |
| `delete <agent_id>`   | Delete an agent                              |

Agent IDs and task IDs tab complete. The `asset`, `artifact`, and `payload` commands are
available here as they are in every connected interpreter, covered in
[Managing Assets](../resource-management/managing-assets.md) and
[Managing Artifacts](../resource-management/managing-artifacts.md).

## Task commands

Everything to do with an agent's tasks is a sub-command of `task`:

| Command                  | Description                                  |
|--------------------------|----------------------------------------------|
| `task list [agent_id]`   | List tasks                                   |
| `task info <task_id>`    | Show details of a task                       |
| `task watch <task_id>`   | Continuously watch a task until it completes |
| `task delete <task_id>`  | Delete a queued or terminal task             |

Sub-command names, agent IDs, and task IDs all tab complete, and each sub-command
carries its own help:

```text
task --help          # list the available sub-commands
task info --help     # show the arguments and examples for one sub-command
```

`task list` with no agent ID lists the tasks of every agent; pass an agent ID to scope
it to one. Inside the interact context it defaults to the agent you are interacting
with. The `-q/--queued`, `-r/--running`, and `-c/--completed` filters can be combined.

`task delete <task_id>` removes a task that is **QUEUED** or in a terminal
**SUCCEEDED**, **FAILED**, or **ERRORED** state. A **RUNNING** task cannot be deleted,
and its current status is reported instead.

## Interacting with a single agent

`interact <agent_id>` drops you into the Interact Agent interpreter for that agent. The
prompt shows the agent's name and ID, and each of the agent's **capabilities** is
registered as its own command. Running one of those capability commands is how you task
the
agent.

```text
agents                 # enter the Agents interpreter
list                   # find the agent that checked in
interact <agent_id>    # scope to that agent
help                   # list this agent's capability commands plus the built in commands
```

Because capabilities become commands, use `help` inside the interact context to see
exactly
what the agent can do, and `help <capability>` for a capability's arguments and value
types. If a capability's name collides with a built in command, the client automatically
deconflicts it by appending a number and warns you of the new name.

The interact context also keeps the agent management commands (`info`, `rename`,
`describe`), the `task` command (whose `list` sub-command defaults to the current
agent), and the resource management commands (`asset`, `artifact`, `payload`). Run
`agents` to return to the Agents interpreter.

## Following task results

Tasking an agent queues a task. You monitor tasks with:

```text
task list              # list tasks (optionally scoped to an agent)
task info <task_id>    # show a task's details and events
task watch <task_id>   # poll a task and print its events until it completes
```

`task watch` supports `--limit` and `--offset` to page through a task's events (for
example `task watch <task_id> --limit 20` tails the last 20 events), and `--interval` to
change the polling interval. `task info` takes the same `--limit` and `--offset`, plus
`--raw` to print event messages as plain text for copying or piping.

While you are interacting with an agent, the client also listens for
`AGENT_TASK_COMPLETED` events and prints a summary of the task's events as they finish,
so
results surface without polling.

## Typical flow

```text
agents                       # an agent has checked in
interact <agent_id>          # scope to it
help                         # discover its capabilities
<capability> <args>          # task the agent
task watch <task_id>         # follow the task to completion
agents                       # return to manage other agents
```
