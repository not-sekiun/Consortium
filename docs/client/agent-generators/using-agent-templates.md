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

| Command                | Description                                              |
|------------------------|----------------------------------------------------------|
| `opt-list`             | List the template's options and their current values     |
| `opt-info <option>`    | Show details of a single option                          |
| `set <option> <value>` | Set an option's value                                    |
| `unset <option>`       | Clear an option's value                                  |
| `reset <option>`       | Reset an option back to its default value                |
| `create`               | Create an agent generator from the current option values |
| `template list`        | List all agent templates                                 |
| `template info`        | Show details of the current template                     |
| `generators`           | Return to the Generators interpreter                     |

Option names tab complete. Values are typed according to each option's expected value
type: use `opt-info <option>` to see the type and any examples, and `help set` for the
value type specification.

## Compatible listeners

An agent template declares the listener types it can connect through. Make sure a
compatible listener is running before you deliver the agent, otherwise it will have
nothing
to connect back to. See [Setting Up Listeners](../listeners/setting-up-listeners.md).

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
opt-list                        # review the configurable options
set callback_host 10.0.0.5      # configure options as needed
set callback_port 8443
create                          # create and start the generator
generators                      # return to the Generators interpreter
payload list                    # find the produced payload
```

With a payload produced, download it and deliver it to a target. See
[Managing Payloads](../resource-management/managing-payloads.md).
