# Managing Client Sessions

A **client session** represents a single authenticated connection to a Consortium
server.
Each session owns its own REST API and Events WebSockets API connections. The client can
hold several sessions at once, letting a single operator work across multiple servers
and
switch between them without restarting.

Client sessions are managed through the `session` command. It is a **core command**, so
sessions can be managed from anywhere in the client: the **Home** interpreter (prompt
`Consortium (Home)`) that the client opens in, the limited **Disconnected** interpreter
it falls back to when no session is connected, and every interpreter in between.

## The session command

Every session operation is a sub-command of `session`:

| Command                                        | Description                                                  |
|------------------------------------------------|--------------------------------------------------------------|
| `session list`                                 | List all current client sessions                             |
| `session connect`                              | Connect to a server, creating a new client session           |
| `session interact <session_id>`                | Switch into a session and start operating against its server |
| `session info [session_id]`                    | Show details of the current or specified session             |
| `session rename [session_id] <name>`           | Give the current or specified session a friendly name        |
| `session describe [session_id] <description>`  | Describe the current or specified session                    |
| `session disconnect [session_id]`              | Disconnect and remove the current or specified session       |

Sub-command names and session IDs tab complete, so you rarely need to type or paste a
full UUID. Each sub-command carries its own help:

```text
session --help           # list the available sub-commands
session connect --help   # show the arguments and examples for one sub-command
```

## Connecting to a server

`session connect` creates a new session. It accepts a configuration file or manual
connection details:

```text
session connect                                      # connect using the default client_config.json
session connect -c path/to/client_config.json        # connect using a custom configuration file
session connect -c -u admin -p admin -rh 127.0.0.1 -rp 9999  # connect with explicit details
```

When a configuration file is supplied, individual flags (`-u`, `-p`, `-rh`, `-rp`)
override the matching field from the file. Pass `-c` without a path to connect without
a configuration file; in that case, all four connection details must be provided.

## Disconnected mode

If the client cannot connect at startup, or once every session has been disconnected, it
enters the Disconnected interpreter (prompt `Consortium`). This mode has no server to
act
against, so it exposes the `session` command along with the core `help`, `alias`, `rc`,
`exec`, `clear`, `banner`, and `exit` commands. The commands that switch interpreters
(`home`, `listeners`, `generators`, and `agents`) are not available.

Unlike the Home interpreter, Disconnected mode has no current session. Sub-commands that
operate on an existing session therefore require its ID rather than defaulting to the
current one:

```text
session info <session_id>
session rename <session_id> <name>
session describe <session_id> <description>
session disconnect <session_id>
```

From disconnected mode, use `session connect` to establish a session and
`session interact` to switch into it, which lands you in that session's Home interpreter.

<div
  data-asciinema-cast="demos/disconnected_interpreter_demo.cast"
  data-cols="105" data-rows="32" data-theme="gruvbox-dark"
></div>

## Switching between sessions

`session interact <session_id>` switches the active session. This is the mechanism behind
holding
multiple servers open at once: connect several sessions, then `session interact` into
whichever one
you want to operate against. All interpreter work (listeners, generators, agents) runs
against the currently interacted session.

## Naming and describing sessions

By default sessions are identified only by their generated UUID. Use `session rename` and
`session describe` to make a set of sessions easier to tell apart:

```text
session rename "production"                          # rename the current session
session rename <session_id> "production"             # rename a specified session
session describe "primary production server"         # describe the current session
session describe <session_id> "primary production server"  # describe a specified session
```

## Ending a session

`session disconnect <session_id>` cleanly tears down a session's REST and WebSockets connections
and removes it from the client. When the last session is disconnected the client returns
to
disconnected mode. Use `exit` to leave the interpreter or close the client entirely.
