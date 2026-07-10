# create_component_project.py

`create_component_project.py` is an interactive scaffolder for framework components. It
generates the directory layout, `manifest.json`, and commented starter code for any of
the four component types, so you can start editing real files instead of assembling the
boilerplate by hand.

## Running the scaffolder

Run it from the repository root in an interactive terminal (it uses full-screen
selection menus, so it needs a real TTY):

```
uv run python scripts/create_component_project.py
```

## What it creates

You first choose a component type, then answer a short series of prompts for the shared
metadata (name, label, description, version, compatible framework version, authors) plus
a few type-specific questions. The scaffolder derives the directory and module names from
the human-readable name and refuses to overwrite an existing component directory.

Every component is written to `consortium/components/<type>/<snake_name>/` with an empty
`__init__.py`, a valid `manifest.json` pointing at the correct entry class, a `README.md`,
and an optional `pyproject.toml` (offered when the component needs third-party
dependencies). The generated module files depend on the type:

| Type             | Generated module files                                        | Manifest entry point                 |
|------------------|---------------------------------------------------------------|--------------------------------------|
| Plugin           | `plugin.py`                                                   | `plugin:Plugin`                      |
| Event Hook       | `event_hook.py`                                               | `event_hook:EventHook`               |
| Listener Profile | `listener_type.py`, `listener_template.py`, `listener.py`     | `listener_template:ListenerTemplate` |
| Agent Profile    | `agent_type.py`, `agent_generator.py`, `agent_template.py`    | `agent_template:AgentTemplate`       |

Type-specific prompts:

- **Plugin**: whether the plugin should `autostart` with the server.
- **Event Hook**: which `EventType` values to subscribe to. The list is read from the live
  `EventType` enum, so it always matches the framework version you are working against.

The generated code mirrors the "complete example" in each component's building guide, with
brief guiding comments and sensible defaults on every required attribute and lifecycle
method.

## Next steps after scaffolding

1. Edit the generated module file(s) to implement your logic.
2. Confirm `manifest.json` has `"enabled": true`.
3. Start your Consortium server; the component is auto-discovered from its `manifest.json`.

## Related guides

The scaffolder produces a starting point; the building guides explain each type in depth:

- [Building a Plugin](../framework/plugins/building-a-plugin/project-setup.md)
- [Building an Event Hook](../framework/event-hooks/building-an-event-hook/project-setup.md)
- [Building a Listener Profile](../framework/listeners/building-a-listener-profile/project-setup.md)
- [Building an Agent Profile](../framework/agents/agents-overview.md)
