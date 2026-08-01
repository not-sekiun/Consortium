# Using Agent Templates

Running `use <template_id>` from the
[Generators interpreter](setting-up-agent-generators.md) enters the **use agent
template**
context. The prompt changes to show which template you are configuring, for example:

```text
Consortium (Generators: 'my_http_agent' (a1b2c3d4-...))
>
```

In this context you set the template's options and then create an agent generator from
them. Each option starts at its default value, and your changes are held locally until
you
run `create`.

## Working with options

| Command                              | Description                                              |
|--------------------------------------|----------------------------------------------------------|
| `option list`                        | List the template's options and their current values     |
| `option info <option>`               | Show details of a single option                          |
| `set <option> <value> [<value> ...]` | Set an option's value                                    |
| `unset <option>`                     | Clear an option's value                                  |
| `reset <option>`                     | Reset an option back to its default value                |
| `name [<name>]`                      | Set the name to give the created generator               |
| `describe [<description>]`           | Set the description to give the created generator        |
| `create`                             | Create an agent generator from the current option values |
| `template list`                      | List all agent templates                                 |
| `template info`                      | Show details of the current template                     |
| `generators`                         | Return to the Generators interpreter                     |

Option names tab complete. Values are typed according to each option's expected value
type: use `option info <option>` to see the type and any examples. Run `set --help` for
the value type specification or `set --help-full` for detailed examples, including
lists, dictionaries, choices, inline type annotations, and `-t/--value-type`.

The `option` and `template` commands group their sub-commands, and each sub-command
carries its own help, for example `option info --help`.

## Compatible listeners

An agent template declares the listener types it can connect through. Make sure a
compatible listener is running before you deliver the agent, otherwise it will have
nothing
to connect back to. See [Setting Up Listeners](../listeners/setting-up-listeners.md).

## Naming the generator

A generator's name and description are **display metadata**, not template options. They
are never derived from the values you `set`: a generator is either given an explicit
name or has a random human-readable one generated for it at creation time.

Stage them with `name` and `describe` before you run `create`:

```text
name "Recon dropper build"         # the created generator will carry this name
describe "for the file server"     # and this description
name                               # clear it again: a random name will be generated
describe                           # clear the staged description
```

Both are staged locally alongside the options and are applied by `create`. They reset
every time you `use` a template, so each trip through a template's context starts clean.

Because these are metadata rather than options, a template is still free to declare an
ordinary option literally called `name` or `description`. Such an option is set with
`set name <value>` like any other and has nothing to do with the generator's display
name: the two never interact.

Renaming a generator that already exists is a different operation, done from the
[Generators interpreter](setting-up-agent-generators.md) with
`rename <generator_id> <name>` and `redescribe <generator_id> <description>`. Both
remain available here, so you can adjust an existing generator without leaving the
template's context.

## Creating the generator

Once the options are configured, `create` produces the generator. By default the new
generator is also started immediately, which produces its payload. Pass `--no-start` (or
`-n`) to create it in a stopped state so you can start it later from the Generators
interpreter.

```text
create           # create the generator and start it
create --no-start # create the generator without starting it
```

## End to end example

```text
generators                      # enter the Generators interpreter
template list                   # find the template you want
use a1b2c3d4-...                # enter the template's context
option list                     # review the configurable options
set callback_host 10.0.0.5      # configure options as needed
set callback_port 8443
name "Recon dropper build"      # optional: name the generator to be created
create                          # create and start the generator
generators                      # return to the Generators interpreter
payload list                    # find the produced payload
```

With a payload produced, download it and deliver it to a target. See
[Managing Payloads](../resource-management/managing-payloads.md).
