# Managing Client Sessions

A **client session** represents a single authenticated connection to a Consortium
server.
Each session owns its own REST API and Events WebSockets API connections. The client can
hold several sessions at once, letting a single operator work across multiple servers
and
switch between them without restarting.

Client sessions are managed from the **Home** interpreter (prompt `Consortium (Home)`)
and
from the limited **Disconnected** interpreter that the client falls back to when no
session
is connected.

## The home interpreter

When the client connects successfully on startup it opens directly in the Home
interpreter. This is the top level context for managing sessions. From here you can list
existing sessions, connect new ones, inspect them, and interact with (switch into) a
session to begin operating against its server.

| Command                   | Description                                                  |
|---------------------------|--------------------------------------------------------------|
| `list`                    | List all current client sessions                             |
| `connect`                 | Connect to a server, creating a new client session           |
| `interact <session_id>`   | Switch into a session and start operating against its server |
| `info <session_id>`       | Show details of a session                                    |
| `rename <session_id>`     | Give a session a friendly name                               |
| `describe <session_id>`   | Attach a description to a session                            |
| `disconnect <session_id>` | Disconnect and remove a session                              |

Session IDs tab complete, so you rarely need to type or paste a full UUID.

## Connecting to a server

The `connect` command creates a new session. It accepts a configuration file or manual
connection details:

```text
connect -c                                   # connect using the default client_config.json
connect -c path/to/client_config.json        # connect using a custom configuration file
connect -u admin -p admin -rh 127.0.0.1 -rp 9999  # connect with explicit details
```

When a configuration file is supplied, individual flags (`-u`, `-p`, `-rh`, `-rp`)
override the matching field from the file. If no configuration file is given, all four
of
the connection details must be provided.

## Disconnected mode

If the client cannot connect at startup, or once every session has been disconnected, it
enters the Disconnected interpreter (prompt `Consortium`). This mode has no server to
act
against, so it only exposes session management commands: `connect`, `list`, `interact`,
`info`, `rename`, `describe`, and `disconnect`, along with the core `help`, `alias`,
`rc`,
`clear`, `banner`, and `exit` commands.

From disconnected mode, use `connect` to establish a session and `interact` to switch
into
it, which lands you in that session's Home interpreter.

<div
  data-asciinema-cast="asciinema/disconnected_interpreter_demo.cast"
  data-cols="100" data-rows="30" data-theme="gruvbox-dark"
></div>

## Switching between sessions

`interact <session_id>` switches the active session. This is the mechanism behind
holding
multiple servers open at once: connect several sessions, then `interact` into whichever
one
you want to operate against. All interpreter work (listeners, generators, agents) runs
against the currently interacted session.

## Naming and describing sessions

By default sessions are identified only by their generated UUID. Use `rename` and
`describe` to make a set of sessions easier to tell apart:

```text
rename <session_id>      # set a short name for the session
describe <session_id>    # set a longer description for the session
```

## Ending a session

`disconnect <session_id>` cleanly tears down a session's REST and WebSockets connections
and removes it from the client. When the last session is disconnected the client returns
to
disconnected mode. Use `exit` to leave the interpreter or close the client entirely.
