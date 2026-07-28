# Client Overview

The Consortium client is an interactive REPL (read, evaluate, print loop) that operators
use to drive a running Consortium server. It authenticates against the server's REST
API,
subscribes to the Events WebSockets API for live updates, and exposes the server's
services through a set of short, self documenting commands.

The client is built with `prompt_toolkit` for the REPL and input handling, `aiohttp` for
the REST API calls, the `websockets` client for the Events API, and `rich` for rendering
tables, panels, and other UI elements.

## Launching the client

Start the client from the project root after the server is already running:

```shell
uv run consortium.py client
```

By default the client reads its connection details from
`data/client/client_config.json` and attempts to connect on startup:

```json hl_lines="4 5" title="client_config.json"
{
  "username": "admin",
  "password": "admin",
  "remote_host": "127.0.0.1",
  "remote_port": 9999
}
```

| Field         | Description                                                                        | Default Value |
|---------------|------------------------------------------------------------------------------------|---------------|
| `username`    | The username of the user that the client will use to authenticate with the server. | `"admin"`     |
| `password`    | The password of the user that the client will use to authenticate with the server. | `"admin"`     |
| `remote_host` | The remote host IP address that the client will connect to.                        | `"127.0.0.1"` |
| `remote_port` | The remote host port that the client will connect to.                              | `9999`        |

!!! important
    The `username` and `password` must correspond to an existing user account in the
    server's [`user_accounts.json`](../server/user-accounts.md) file.

To use a configuration file from a different location, pass `-c/--client-config`:

```shell
uv run consortium.py client -c path/to/custom_client_config.json
```

Pass `--debug` to raise the log level to `DEBUG`. Client logs are written to
`data/client/logs/`.

If the initial connection succeeds the client opens in the **Home** interpreter. If it
fails, the client starts in **disconnected mode** instead (see
[Managing Client Sessions](client-sessions/managing-client-sessions.md)).

## Interpreters and context

The client is organized around **interpreters**. An interpreter is a mode that scopes
the
prompt to a particular kind of work and loads only the commands relevant to it.
Switching
interpreters is how you move between managing sessions, listeners, generators, and
agents.

| Interpreter           | Prompt                            | Purpose                                                     |
|-----------------------|-----------------------------------|-------------------------------------------------------------|
| Home                  | `Consortium (Home)`               | Manage client sessions across one or more servers           |
| Disconnected          | `Consortium`                      | A limited mode entered when no session is connected         |
| Listeners             | `Consortium (Listeners)`          | List, start, stop, and manage listeners                     |
| Use Listener Template | `Consortium (Listeners: <name>)`  | Configure a listener template and create a listener from it |
| Generators            | `Consortium (Generators)`         | Manage agent generators                                     |
| Use Agent Template    | `Consortium (Generators: <name>)` | Configure an agent template and create a generator from it  |
| Agents                | `Consortium (Agents)`             | List agents and inspect their tasks                         |
| Interact Agent        | `Consortium (Agents: <name>)`     | Task a single agent through its capabilities                |

The current interpreter is always reflected in the prompt, colored by area (listeners in
blue, generators in green, agents in red), so you can tell your context at a glance.

## Moving between interpreters

From any connected interpreter, a set of core navigation commands switch context:

| Command      | Switches to            |
|--------------|------------------------|
| `home`       | Home interpreter       |
| `listeners`  | Listeners interpreter  |
| `generators` | Generators interpreter |
| `agents`     | Agents interpreter     |

The `use` and `interact` commands enter the more specific "use template" and "interact
agent" interpreters, and running them for a resource drops you into its context. Running
`listeners`, `generators`, or `agents` again returns you to the parent interpreter.

A typical operator session flows like this:

```text
home                      # inspect and pick a client session
listeners                 # move into the listeners interpreter
  use <listener_template> # configure a template and create a listener
generators                # move into the generators interpreter
  use <agent_template>    # configure a template and create a generator
agents                    # once an agent checks in
  interact <agent_id>     # task the agent
```

## Commands and help

Every command parses its own arguments internally and ships with a help menu. There is
no
need to memorize argument formats: use `help` at any time.

```text
help            # list every command available in the current interpreter, grouped by area
help <command>  # show the full usage, arguments, and examples for a single command
```

The client provides tab completion for command names and for their arguments (session
IDs, listener IDs, template IDs, option names, and so on). Completions update live as
the
server emits events, so newly created resources become completable without a manual
refresh.

Other core commands available across interpreters:

| Command     | Description                                                  |
|-------------|--------------------------------------------------------------|
| `clear`     | Clear the terminal screen                                    |
| `banner`    | Reprint the startup banner                                   |
| `alias`     | Create and manage command aliases                            |
| `rc <file>` | Run commands from a resource file in the current interpreter |
| `exit`      | Exit the current interpreter or the client                   |

See [Aliases and Resource Files](aliases-and-resource-files.md) for automating repeated
command sequences.

## Resource management commands

Assets, artifacts, and payloads are **repository resources**: they belong to the server
rather than to any one interpreter. Each is managed through a single command whose
operations are sub-commands, and all three are available in every connected interpreter,
listed together under the **Resource Management Commands** group in `help`.

| Command    | Description                                                       |
|------------|-------------------------------------------------------------------|
| `asset`    | List, inspect, upload, download, rename, describe, remove assets  |
| `artifact` | List, inspect, download, rename, describe, remove artifacts       |
| `payload`  | List, inspect, download, rename, describe, remove payloads        |

```text
asset list                   # run a sub-command
asset --help                 # list a command's sub-commands
asset upload --help          # show one sub-command's arguments and examples
```

Sub-command names and resource IDs tab complete, and the completions stay current as the
server emits resource events. See
[Managing Assets](resource-management/managing-assets.md),
[Managing Artifacts](resource-management/managing-artifacts.md), and
[Managing Payloads](resource-management/managing-payloads.md).

## Where to go next

- [Managing Client Sessions](client-sessions/managing-client-sessions.md): connect to
  servers and juggle multiple sessions.
- [Setting Up Listeners](listeners/setting-up-listeners.md) and
  [Using Listener Templates](listeners/using-listener-templates.md): stand up the
  network components agents connect through.
- [Setting Up Agent Generators](agent-generators/setting-up-agent-generators.md) and
  [Using Agent Templates](agent-generators/using-agent-templates.md): produce agents.
- [Tasking Agents](agents/tasking-agents.md): drive agents once they check in.
- [Managing Assets](resource-management/managing-assets.md),
  [Managing Artifacts](resource-management/managing-artifacts.md), and
  [Managing Payloads](resource-management/managing-payloads.md): work with the files
  that move between the client, the server, and your targets.
