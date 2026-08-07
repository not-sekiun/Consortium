# Persistent Listeners Plugin

Saves the listeners that exist when the server shuts down and recreates them on the
next startup.

- Label: `consortium.plugins.persistent_listeners_plugin`
- Autostart: yes
- Enabled by default: yes

## What it does

On shutdown (`on_stopped`) the plugin walks
`services.listeners_service.get_all_listeners()` and writes each listener to
`persistent_listeners.json` in the plugin's root directory, grouped by the label of the
listener template that created it:

```json
{
    "consortium.listener_templates.http_listener": [
        {
            "previously_running": true,
            "name": "primary-http",
            "description": "Main HTTP listener",
            "parameters": {"port": 8080}
        }
    ]
}
```

On startup (`on_started`) it reads that file back and, for each entry, recreates the
listener from the matching listener template with the saved name, description and
parameters. Entries with `"previously_running": true` are also started; the rest are
only created.

A missing file is created as `{}`, and an empty file is treated as no persisted
listeners. If a listener template with the recorded label no longer exists (renamed or
removed profile), the entry is skipped with a warning rather than failing startup.

`on_running` simply awaits `self.stop_event`. The plugin has to stay in the running
state for the framework to call `on_stopped`, which is where the file is written.

## Usage

Enabled by default via `manifest.json`. Nothing else is required: create and start
listeners as usual and they will come back after a restart.

To reset persistence, stop the server and either delete `persistent_listeners.json` or
write `{}` into it.

## Notes

- The snapshot is taken only during a clean shutdown. If the process is killed, the
  file keeps whatever was written at the previous clean shutdown.
- Listeners are matched by template label, so relabelling a listener template orphans
  its saved entries.
- Listener parameters are stored verbatim in plaintext JSON. Anything sensitive passed
  as a listener parameter ends up in this file.
