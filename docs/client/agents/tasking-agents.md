# Tasking Agents

Once a payload has been delivered and executed on a target, the agent connects back
through
its listener and checks in. From that point you manage and task it from the client. Two
interpreters are involved:

- The **Agents** interpreter (prompt `Consortium (Agents)`) lists all agents, inspects
  their tasks, and manages assets.
- The **Interact Agent** interpreter (prompt `Consortium (Agents: <name>)`) scopes you
  to a
  single agent so you can task it through its capabilities.

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
| `t-list [agent_id]`   | List tasks                                   |
| `t-info <task_id>`    | Show details of a task                       |
| `watch <task_id>`     | Continuously watch a task until it completes |
| `rename <agent_id>`   | Rename an agent                              |
| `describe <agent_id>` | Attach a description to an agent             |

Agent IDs and task IDs tab complete. The Agents interpreter also carries the asset
commands
covered in [Managing Assets](managing-assets.md).

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
`describe`, `t-list`), the task inspection commands (`t-info`, `watch`), and the asset
commands. Run `agents` to return to the Agents interpreter.

## Following task results

Tasking an agent queues a task. You monitor tasks with:

```text
t-list                 # list tasks (optionally scoped to an agent)
t-info <task_id>       # show a task's details and events
watch <task_id>        # poll a task and print its events until it completes
```

`watch` supports `--limit` and `--offset` to page through a task's events (for example
`watch <task_id> --limit 20` tails the last 20 events), and `--interval` to change the
polling interval.

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
watch <task_id>              # follow the task to completion
agents                       # return to manage other agents
```
