# manage_components.py

`manage_components.py` is the component project manager: an interactive tool for the
whole lifecycle of framework components (listeners, agents, plugins, and event hooks)
under `consortium/components/`. From a single menu you can scaffold a new component,
enable, disable, and inspect existing ones, install a component from a local directory,
a git repository, or an HTTP archive, and uninstall a component by deleting its folder.

Component creation, which used to live in a standalone `create_component_project.py`
script, is now the manager's **Create** action, so there is one entry point for every
component task.

## Running the tool

Run it from the repository root in an interactive terminal (it uses full-screen
selection menus, so it needs a real TTY):

```
uv run python scripts/manage_components.py
```

The tool opens on a main menu with the four actions below plus **Exit**. You can move
between actions freely; each returns to the main menu when it finishes or is cancelled.

## How components are discovered

For the manage, install, and uninstall actions, the tool walks each component-kind
directory (`listeners/`, `agents/`, `plugins/`, `event_hooks/`) under
`consortium/components/` recursively for `manifest.json` files. Each manifest is
schema-validated against the same shape every `ComponentLoaderService` subclass expects
(`entry_point` and `enabled` are required). Manifests with invalid JSON or that fail the
schema are listed separately as skipped rather than treated as manageable components.

## Create a new component

**Create a new component** scaffolds a ready-to-edit project so you start by editing
real files instead of assembling boilerplate by hand. You first choose a component type,
then answer a short series of prompts for the shared metadata (name, label, description,
version, compatible framework version, authors) plus a few type-specific questions. The
directory and module names are derived from the human-readable name, and the scaffolder
refuses to overwrite an existing component directory (including an empty one).

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
method. After scaffolding, edit the generated module file(s) to implement your logic,
confirm `manifest.json` has `"enabled": true`, and start your Consortium server; the
component is auto-discovered from its `manifest.json`.

## Manage components (enable/disable, view info)

**Manage components** opens a list of every valid component showing its kind, name, and a
coloured status (**enabled**, **disabled**, or **invalid**). In this list:

- **Space** toggles the highlighted component's `enabled` flag. The change is written back
  to that component's `manifest.json` immediately, preserving the rest of the manifest.
- **Enter** opens the information view for the highlighted component.

The information view first shows the manifest-derived facts (kind, name, folder, entry
point, and whether it is enabled), which are always available. It then imports the
component's entry-point class and lists its class-level metadata attributes (`label`,
`name`, `description`, `version`, `compatible_framework_version`, `authors`,
`component_dependencies`). The field list is read from the framework's
`ComponentMetadataModel` when it can be imported, so the view stays in sync with it. If
the component cannot be imported (for example a syntax or import error in its module), the
reason is shown in place of the metadata rather than crashing the manager.

## Install a component (local / git / HTTP archive)

**Install a component** copies an existing component project into the components tree. You
first pick the target kind (`Listeners`, `Agents`, `Plugins`, or `Event Hooks`), then a
source:

- **Local directory**: a path to a component project on disk.
- **Git repository (clone)**: a repository URL and optional branch/tag, shallow-cloned into
  a temporary directory.
- **HTTP hosting (archive)**: a URL to a `.zip`, `.tar`, or `.tar.gz` archive, downloaded
  and extracted into a temporary directory. Archive members with absolute paths or parent
  traversal are rejected so an extract can never write outside the temp directory.

A component project is any directory containing a `manifest.json`. If the source contains
more than one, you choose which to install. The manifest is schema-validated first; if it
is invalid you are asked to confirm before installing anyway. You then choose the
destination folder name (defaulting to the source folder name).

The install never overwrites anything: if the destination directory already exists, or any
file the copy would create already exists, the install is denied and the conflicting paths
are listed. Build and VCS artifacts (`.git`, `__pycache__`, `*.pyc`, and the various tool
caches) are excluded from the copy. Before writing, the tool prints a review panel (kind,
source, destination) and asks for a final confirmation. Any temporary clone or extract
directory is always cleaned up afterwards.

## Uninstall a component (delete)

**Uninstall a component** lists every discovered component (valid and invalid) and, after
you select one, permanently deletes its entire folder. Because this cannot be undone, the
tool shows the exact folder to be removed and asks for a confirmation that defaults to
**No**.

## Related guides

The manager produces a starting point; the building guides explain each type in depth:

- [Building a Plugin](../framework-api/plugins/building-a-plugin/project-setup.md)
- [Building an Event Hook](../framework-api/event-hooks/building-an-event-hook/project-setup.md)
- [Building a Listener Profile](../framework-api/listeners/building-a-listener-profile/project-setup.md)
- [Building an Agent Profile](../framework-api/agents/agents-overview.md)
