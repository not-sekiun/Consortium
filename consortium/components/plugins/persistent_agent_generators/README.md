# Persistent Agent Generators Plugin

Saves the agent generators that exist when the server shuts down and recreates them on
the next startup.

- Label: `consortium.plugins.persistent_agent_generators_plugin`
- Autostart: yes
- Enabled by default: yes

## What it does

On shutdown (`on_stopped`) the plugin walks
`services.agent_generators_service.get_all_agent_generators()` and writes each generator
to `persistent_agent_generators.json` in the plugin's root directory, grouped by the
label of the agent template that created it:

```json
{
    "consortium.agent_templates.http_agent": [
        {
            "name": "windows-http",
            "description": "HTTP agent generator for Windows targets",
            "parameters": {"callback_host": "10.0.0.1"}
        }
    ]
}
```

On startup (`on_started`) it reads that file back and recreates each generator from the
matching agent template with the saved name, description and parameters.

A missing file is created as `{}`, and an empty file is treated as no persisted
generators. If an agent template with the recorded label no longer exists (renamed or
removed profile), the entry is skipped with a warning rather than failing startup.

`on_running` simply awaits `self.stop_event`. The plugin has to stay in the running
state for the framework to call `on_stopped`, which is where the file is written.

## Usage

Enabled by default via `manifest.json`. Nothing else is required: create agent
generators as usual and they will come back after a restart.

To reset persistence, stop the server and either delete
`persistent_agent_generators.json` or write `{}` into it.

## Notes

- Unlike [persistent_listeners](../persistent_listeners/README.md), no run state is
  tracked. Generators are only recreated, never started.
- The snapshot is taken only during a clean shutdown. If the process is killed, the
  file keeps whatever was written at the previous clean shutdown.
- Generators are matched by template label, so relabelling an agent template orphans its
  saved entries.
- Generator parameters are stored verbatim in plaintext JSON. Anything sensitive passed
  as a generator parameter ends up in this file.
