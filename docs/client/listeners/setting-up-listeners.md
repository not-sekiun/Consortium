# Setting Up Listeners

Listeners are the persistent, server side network components that agents connect
through.
The **Listeners** interpreter (prompt `Consortium (Listeners)`) is where you view
listener
templates, create listeners from them, and manage the lifecycle of running listeners.

Switch into it from any connected interpreter with the `listeners` command.

## Listener templates versus listeners

There are two related concepts:

- A **listener template** is a reusable definition that describes a kind of listener and
  the options needed to configure one. Templates are loaded on the server from listener
  profiles. See the
  framework [Listeners Overview](../../framework/listeners/listeners-overview.md)
  for how they are authored.
- A **listener** is a concrete, running instance created from a template with a specific
  set of option values.

You do not create listener templates from the client: you create listeners *from*
templates. Configuring a template and producing a listener happens in the "use listener
template" context, covered in [Using Listener Templates](using-listener-templates.md).

## The listeners interpreter

On entry, the Listeners interpreter lists all current listeners and all available
listener
templates. It also subscribes to `LISTENER_CREATED` and `LISTENER_REMOVED` events so its
listings and tab completion stay current as listeners come and go.

Commands available here:

| Command                                | Description                                                     |
|----------------------------------------|-----------------------------------------------------------------|
| `list`                                 | List all listeners                                              |
| `template list`                        | List all listener templates                                     |
| `template info <template_id>`          | Show details of a listener template                             |
| `use <template_id>`                    | Enter the template's context to configure and create a listener |
| `info <listener_id>`                   | Show details of a listener                                      |
| `start <listener_id>`                  | Start a non running listener                                    |
| `stop <listener_id>`                   | Stop a running listener                                         |
| `cancel <listener_id>`                 | Cancel a listener                                               |
| `update <listener_id> <param> <value>` | Update a running listener's parameters                          |
| `rename <listener_id> <name>`          | Rename a listener                                               |
| `describe <listener_id> <description>` | Attach a description to a listener                              |
| `delete <listener_id>`                 | Delete a listener                                               |

Listener IDs, template IDs, and (for `update`) parameter names all tab complete.

## The typical workflow

1. Enter the Listeners interpreter with `listeners`.
2. Browse the available templates with `template list`, and inspect one with
   `template info <template_id>`.
3. Enter its context with `use <template_id>` to configure options and create a
   listener.
   This is described in [Using Listener Templates](using-listener-templates.md).
4. Back in the Listeners interpreter, confirm the listener is running with `list` and
   `info <listener_id>`.

## Managing running listeners

Once a listener exists you control its lifecycle directly:

```text
start <listener_id>    # start a listener that is not running
stop <listener_id>     # stop a running listener
update <listener_id> <param> <value>   # change a parameter on a running listener
delete <listener_id>   # remove the listener entirely
```

A listener's compatible agent types determine which agents can connect through it. When
you move on to producing agents, the agent template you use must declare a compatible
listener type.
See [Using Agent Templates](../agent-generators/using-agent-templates.md).
