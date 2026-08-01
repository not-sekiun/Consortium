# Aliases and Resource Files

The client provides two facilities for cutting down on repetitive typing: **aliases**
for
shortening individual commands, and **resource files** for replaying a whole sequence of
commands. Both are available in every interpreter through the core `alias` and `rc`
commands.

## Aliases

The `alias` command creates named shortcuts for commands. Aliases are persisted to
`data/client/aliases.json`, so they survive across client restarts.

| Sub command                       | Description                    |
|-----------------------------------|--------------------------------|
| `alias list`                      | List all currently set aliases |
| `alias set <name> "<command>"`    | Set an alias                   |
| `alias set -g <name> "<command>"` | Set a global alias             |
| `alias unset <name>`              | Remove an alias                |

```text
alias list
alias set ll "list"
alias set -g admin_login "connect -u admin -p admin -rh 127.0.0.1 -rp 9999"
alias unset ll
```

There are two kinds of alias:

- A **local alias** (without `-g`) only expands when it is the first token of a line. It
  behaves like a command shortcut and will not expand elsewhere.
- A **global alias** (`-g`) expands as a token anywhere in the line, which is useful for
  abbreviating frequently typed arguments.

The terms local and global describe where an alias can expand in a command, not which
interpreter can use it. Both kinds are available in every interpreter. For example, a
local alias only replaces the command name at the beginning of the line:

```text
alias set ll "session list"
ll                     # Expands to: session list
help ll                # Does not expand ll
```

A global alias can replace a matching token at the beginning, middle, or end of the
line:

```text
alias set -g server "-rh 127.0.0.1 -rp 9999"
session connect -u admin -p admin server
# Expands to: session connect -u admin -p admin -rh 127.0.0.1 -rp 9999
```

If you set an alias whose name already exists, the client asks before overwriting it.

### Alias configuration

The alias file contains separate `local_aliases` and `global_aliases` objects. Both
objects are required, even when one of them is empty. Each entry maps an alias name to
the command text that replaces it:

```json title="default client alias configuration at data/client/aliases.json"
{
  "local_aliases": {
    "?": "help",
    "!": "exec"
  },
  "global_aliases": {}
}
```

Aliases created with `alias set` are local aliases, while aliases created with
`alias set -g` are global aliases. Keep each alias name in only one object. The client
loads this file when it starts, so restart the client after editing it directly.

## Resource files

The `rc` command runs a batch of commands from a file in the current interpreter. This
is
useful for scripting a standard setup, such as bringing up a listener and a generator in
one step.

```text
rc setup.txt
```

A resource file contains one command per line. Blank lines and lines beginning with `#`
are
treated as comments and ignored:

```text title="setup.txt"
# Stand up a listener
listeners
use a1b2c3d4-...
set port 8443
create
listeners

# Produce an agent
generators
use e5f6a7b8-...
set callback_port 8443
create
```

Commands run from a resource file execute in the current interpreter context, and their
prompt is prefixed with `[RC]` so you can tell replayed commands apart from ones you
type
interactively.
