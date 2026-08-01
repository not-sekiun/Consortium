# Using Listener Templates

Running `use <template_id>` from the [Listeners interpreter](setting-up-listeners.md)
enters the **use listener template** context. The prompt changes to show which template
you are configuring, for example:

```text
Consortium (Listeners: my_tcp_listener (a1b2c3d4-...))
>
```

In this context you set the template's options to the values you want and then create a
listener from them. Each option starts at its default value, and your changes are held
locally until you run `create`.

## Working with options

| Command                              | Description                                          |
|--------------------------------------|------------------------------------------------------|
| `option list`                        | List the template's options and their current values |
| `option info <option>`               | Show details of a single option                      |
| `set <option> <value> [<value> ...]` | Set an option's value                                |
| `unset <option>`                     | Clear an option's value                              |
| `reset <option>`                     | Reset an option back to its default value            |
| `name [<name>]`                      | Set the name to give the created listener            |
| `describe [<description>]`           | Set the description to give the created listener     |
| `create`                             | Create a listener from the current option values     |
| `template list`                      | List all listener templates                          |
| `template info`                      | Show details of the current template                 |
| `listeners`                          | Return to the Listeners interpreter                  |

Option names tab complete. Values are typed according to each option's expected value
type: use `option info <option>` to see the type and any examples. Run `set --help` for
the value type specification or `set --help-full` for detailed examples, including
lists, dictionaries, choices, inline type annotations, and `-t/--value-type`.

The `option` and `template` commands group their sub-commands, and each sub-command
carries its own help, for example `option info --help`.

## Naming the listener

A listener's name and description are **display metadata**, not template options. They
are never derived from the values you `set`: a listener is either given an explicit name
or has a random human-readable one generated for it at creation time.

Stage them with `name` and `describe` before you run `create`:

```text
name "Edge TCP listener"           # the created listener will carry this name
describe "external perimeter"      # and this description
name                               # clear it again: a random name will be generated
describe                           # clear the staged description
```

Both are staged locally alongside the options and are applied by `create`. They reset
every time you `use` a template, so each trip through a template's context starts clean.

Because these are metadata rather than options, a template is still free to declare an
ordinary option literally called `name` or `description`. Such an option is set with
`set name <value>` like any other and has nothing to do with the listener's display
name: the two never interact.

Renaming a listener that already exists is a different operation, done from the
[Listeners interpreter](setting-up-listeners.md) with `rename <listener_id> <name>` and
`redescribe <listener_id> <description>`. Both remain available here, so you can adjust
an existing listener without leaving the template's context.

## Creating the listener

Once the options are configured, `create` produces the listener. By default the new
listener is also started immediately. Pass `--no-start` (or `-n`) to create it in a
stopped
state so you can start it later from the Listeners interpreter.

```text
create           # create the listener and start it
create --no-start # create the listener without starting it
```

## End to end example

```text
listeners                       # enter the Listeners interpreter
template list                   # find the template you want
use a1b2c3d4-...                # enter the template's context
option list                     # review the configurable options
set host 0.0.0.0                # configure options as needed
set port 8443
name "Edge TCP listener"        # optional: name the listener to be created
create                          # create and start the listener
listeners                       # return to the Listeners interpreter to verify
list
```

With a listener running, the next step is to produce agents that connect through it. See
[Setting Up Agent Generators](../agent-generators/setting-up-agent-generators.md).
