# Framework Overview

The framework is the extensible core of Consortium. Everything an operator interacts
with at runtime (listeners, agents, background plugins, and event hooks) is built from
**components**: self-contained projects that live under `consortium/components/` and are
discovered and loaded when the server starts.

This page covers the concepts that are shared across every component type: how a
component project is laid out, how components are identified (the difference between
labels, names, and IDs), and how dependencies are declared and resolved. For more
information on each type of component, check the following pages:

- [Listeners Overview](listeners/listeners-overview.md)
- [Agents Overview](agents/agents-overview.md)
- [Plugins Overview](plugins/plugins-overview.md)
- [Event Hooks Overview](event-hooks/event-hooks-overview.md)

!!! tip "Scaffold a component instead of writing it by hand"

    The [`create_component_project.py`](../scripts/create-component-project.md)
    scaffolder generates a ready-to-edit project for any of the four component types,
    with the directory, `manifest.json`, and commented reference stubs already in place.
    The concepts below still apply, and understanding them makes the generated files
    much easier to work with.

## The four component types

| Type       | Directory                   | Entry point                          | What it does                                                    |
|------------|-----------------------------|--------------------------------------|-----------------------------------------------------------------|
| Listener   | `components/listeners/`     | `listener_template:ListenerTemplate` | Runs a network server that agents connect through               |
| Agent      | `components/agents/`        | `agent_template:AgentTemplate`       | Builds agent payloads and handles their tasks and results       |
| Plugin     | `components/plugins/`       | `plugin:Plugin`                      | Runs a persistent background loop alongside the server          |
| Event hook | `components/event_hooks/`   | `event_hook:EventHook`               | Reacts to discrete framework events as they fire                |

Listeners and agents are **profiles**: several cooperating classes spread across a few
files. Plugins and event hooks are a single class in a single file. Regardless of type,
every component follows the same discovery and identity rules described below.

## Component project structure

Each component is a directory under its type's folder. Every component directory contains
a `manifest.json`, plus the module file(s) that hold the entry point class:

```
consortium/components/plugins/my_plugin/
├── manifest.json
└── plugin.py
```

`manifest.json` is what the loader looks for when it walks the components tree. It points
at the entry point class and declares whether the component should be loaded:

```json
{
  "entry_point": "plugin:Plugin",
  "enabled": true
}
```

- `entry_point` is `<module>:<Class>`, where `<module>` is the module file (without the
  `.py`) relative to the component directory. Each type has a conventional entry point
  class name, listed in the table above.
- `enabled` controls whether the loader picks the component up. Set it to `false` to
  leave a component in place but unloaded.

The loader recursively searches each type directory for `manifest.json` files, so a
component folder can sit at any depth (for example
`components/agents/consortium/http/`), not just directly under the type folder.

## Identity: labels, names, and IDs

Every component carries three distinct kinds of identifier, and they are easy to confuse.
They exist for different reasons and are set at different times.

| Identifier   | Example                          | Set by            | Stable?                         | Purpose                                                         |
|--------------|----------------------------------|-------------------|---------------------------------|-----------------------------------------------------------------|
| **Label**    | `consortium.plugins.agent_report`| Component author  | Yes (fixed for the component)   | Globally unique reference used for persistence and dependencies |
| **Name**     | `Agent Report Plugin`            | Author / operator | No (freely editable)            | Human-readable display text                                     |
| **ID**       | `f47ac10b-...` (`uuid.UUID`)     | Framework         | No (new one every run)          | Identifies one running instance for the duration of the server  |

### Label

The `label` is the component's stable, globally unique identifier. It is a class
attribute the author declares, and it is validated at class-definition time (a missing or
empty label fails at import, not at runtime). Because it never changes, the framework
uses it wherever a component must be referenced durably:

- In persisted configuration and across server restarts.
- As the key that other components target when they declare a dependency (see
  [Component dependencies](#component-dependencies-on-other-components)).

Because labels must be unique and stable across an entire installation, they follow a
**reverse-DNS naming convention**:

```
<namespace> . <component-type> . <component-name>
```

```text
consortium.plugins.agent_report
consortium.listeners.tcp_json
consortium.event_hooks.agent_activity_tracker
acme.agents.recon_agent
```

- `<namespace>` is a vendor or author namespace (the built-in components use
  `consortium`). Pick your own for components you publish, so your labels never collide
  with anyone else's.
- `<component-type>` is one of `listeners`, `agents`, `plugins`, or `event_hooks`.
- `<component-name>` is a `snake_case` name for the specific component.

The label is deliberately **not** derived from the directory path or the file name, so
you can move or rename a component's folder without breaking references to it. The label
is the contract; the folder layout is just where the code happens to live.

### Name

The `name` is the human-readable display text shown in the client and logs. It is
free-form and can be changed at any time without consequence, because nothing references
a component by its name.

- For plugins and event hooks, `name` is a class attribute the author sets.
- For listener and agent **instances**, the operator sets the name when they create the
  instance (a single agent profile can produce many differently-named running agents).

If a component omits `name`, the framework falls back to using the `label` as the display
name.

### ID

An **ID** identifies a single running instance, not the component definition. Each running
plugin, listener, agent, or event hook is assigned a `uuid.UUID` (`self.plugin_id`,
`self.listener_id`, `self.agent_id`, `self.event_hook_id`) when it is instantiated. IDs
are generated fresh every time and are **not** stable across restarts, so they are only
useful for addressing a live instance during the current server session, never for
durable references.

### Label vs. name vs. ID at a glance

- Use the **label** when you need to refer to a component definition durably (config,
  dependencies). One label, fixed forever.
- Use the **name** for anything a human reads. Cosmetic, editable, non-unique.
- Use the **ID** to address one live instance right now. Ephemeral, framework-assigned.

!!! note "Type names are a different thing"

    `ListenerType.name` and `AgentType.name` (for example `tcp_json` or `recon_agent`)
    are not component labels. They name a transport or agent *family* and are used to
    match agents to the listeners they may connect through (an agent template lists
    `compatible_listener_types = {"tcp_json"}`). A type name identifies a family across
    profiles; a label identifies a single component project. See
    [ListenerType](listeners/building-a-listener-profile/listener-type.md) and
    [AgentType](agents/building-an-agent-profile/agent-type.md).

## Shared metadata

Alongside `label` and `name`, every component entry class declares the same core
metadata. It is all validated at class-definition time, so malformed values fail at
import rather than surfacing later at runtime.

| Attribute                      | Type       | Default    | Description                                                        |
|--------------------------------|------------|------------|--------------------------------------------------------------------|
| `label`                        | `str`      | (required) | Stable reverse-DNS identifier (see above)                          |
| `name`                         | `str`      | `label`    | Human-readable display name                                        |
| `description`                  | `str`      | `""`       | Short description of what the component does                       |
| `version`                      | `str`      | `None`     | The component's own version, a PEP 440 version                     |
| `compatible_framework_version` | `str`      | `None`     | PEP 440 specifier for the framework versions this component supports |
| `authors`                      | `set[str]` | `set()`    | Author names                                                       |

`version` is the component's own version string (for example `"0.1.0"`), parsed as a
[PEP 440 version](https://peps.python.org/pep-0440/). It is what other components match
against when they depend on this one.

`compatible_framework_version` is a
[PEP 440 version specifier](https://peps.python.org/pep-0440/) (for example `">=0.1.0"`).
At load time the framework compares the running framework version against this specifier
and refuses to load a component that does not cover it. Leave it unset for no constraint,
or pin it when the component relies on a specific framework API.

## Dependency management

A component can depend on two very different things, and the framework treats them
separately:

1. **Third-party Python packages** from PyPI (declared in `pyproject.toml`).
2. **Other Consortium components** (declared as `component_dependencies` on the class).

### Third-party dependencies (PyPI packages)

If a component imports a package that is not part of the standard library or the
framework, declare it in a `pyproject.toml` sitting next to the manifest:

```toml
[project]
name = "consortium.my-plugin"
dependencies = [
    "aiohttp",
    "some-package>=1.0",
]
```

At load time the framework reads `[project].dependencies` and, for each entry, checks
that the package is **already importable in the server's environment** and that its
installed version satisfies the specifier. If a dependency is missing or the wrong
version, the component is not loaded and the framework reports why.

!!! warning "The framework does not install packages for you"

    Declaring a dependency in `pyproject.toml` is a **check**, not an install step. The
    framework verifies the package is present; it never fetches anything. You must install
    third-party dependencies into the same environment the server runs in yourself. For
    the standard `uv`-managed setup that means `uv add <package>` (then `uv sync`), which
    matches how the rest of the project manages dependencies.

### Component dependencies (on other components)

A component can also require that another Consortium component is present and loaded
first. These are declared as `component_dependencies`, a set of
[PEP 508 requirement](https://peps.python.org/pep-0508/) strings whose names are the
**labels** of the components you depend on:

```python
class Plugin(BasePlugin):
    label = "consortium.plugins.agent_report"
    ...
    component_dependencies = {
        "consortium.plugins.persistent_listeners>=0.1.0",
    }
```

Because a label is stable and unique, it is a safe thing to depend on. At load time the
framework:

1. Confirms every named dependency label is registered, and that its `version` satisfies
   the specifier (missing or incompatible dependencies cause the dependent component to
   be skipped, not the whole load to fail).
2. Builds a dependency graph from the surviving components and topologically sorts it, so
   a component is always started after everything it depends on.
3. Aborts the load if the graph contains a cycle.

## Where to go next

- Build one end to end: [Listeners](listeners/listeners-overview.md),
  [Agents](agents/agents-overview.md), [Plugins](plugins/plugins-overview.md),
  [Event Hooks](event-hooks/event-hooks-overview.md).
- Skip the boilerplate with the
  [component scaffolder](../scripts/create-component-project.md).
