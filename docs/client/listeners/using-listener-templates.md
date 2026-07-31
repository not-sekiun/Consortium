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

| Command                | Description                                          |
|------------------------|------------------------------------------------------|
| `opt-list`             | List the template's options and their current values |
| `opt-info <option>`    | Show details of a single option                      |
| `set <option> <value>` | Set an option's value                                |
| `unset <option>`       | Clear an option's value                              |
| `reset <option>`       | Reset an option back to its default value            |
| `create`               | Create a listener from the current option values     |
| `lt-info`              | Show details of the current template                 |
| `listeners`            | Return to the Listeners interpreter                  |

Option names tab complete. Values are typed according to each option's expected value
type: use `opt-info <option>` to see the type and any examples, and `help set` for the
value type specification.

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
lt-list                         # find the template you want
use a1b2c3d4-...                # enter the template's context
opt-list                        # review the configurable options
set host 0.0.0.0                # configure options as needed
set port 8443
create                          # create and start the listener
listeners                       # return to the Listeners interpreter to verify
list
```

With a listener running, the next step is to produce agents that connect through it. See
[Setting Up Agent Generators](../agent-generators/setting-up-agent-generators.md).
