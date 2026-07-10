# Project Setup

This guide builds a complete listener profile step by step. The profile we will write is
a **TCP JSON Listener**: a raw TCP server that exchanges newline-delimited JSON messages
with connected agents. By the time we reach
[Complete Listener Profile](complete-listener-profile.md), it will demonstrate every
major listener concept, from naming a transport to fulfilling the full agent-listener
protocol.

## The three classes

A listener is never a single class. Every listener profile is three cooperating classes,
written together and loaded as one unit. We will build them in order, one page at a time:

| Step | Class              | File                   | Role                                              |
|------|--------------------|------------------------|---------------------------------------------------|
| 1    | `ListenerType`     | `listener_type.py`     | Names the transport family agents connect through |
| 2    | `ListenerTemplate` | `listener_template.py` | Configuration schema and factory for listeners    |
| 3    | `Listener`         | `listener.py`          | The running network server                        |

Between steps 2 and 3 we pause on [The Agent-Listener Protocol](listener-protocol.md):
the contract the `Listener` class exists to satisfy.

!!! tip "Scaffold it instead"

    Rather than creating these files by hand, you can generate a ready-to-edit listener
    profile (directory, `manifest.json`, and commented `listener_type.py`,
    `listener_template.py`, and `listener.py` files) with the
    [`create_component_project.py`](../../../scripts/create-component-project.md)
    scaffolder. This guide is still worth reading to understand what the generated files
    do.

## Setting up the project files

Each listener profile lives in its own directory under
`consortium/components/listeners/`. Create one for the profile now:

```
consortium/components/listeners/tcp_json/
├── manifest.json
├── listener_type.py
├── listener_template.py
└── listener.py
```

`manifest.json` points the component loader at the profile entry class. The entry point
format is `<module>:<class>`, and by convention it must always be
`listener_template:ListenerTemplate`:

```json
{
    "entry_point": "listener_template:ListenerTemplate",
    "enabled": true
}
```

`enabled` controls whether the loader picks up the profile when the server starts. Set it
to `false` to leave the profile in place but unloaded.

Continue to [ListenerType](listener-type.md) to declare the transport family.
