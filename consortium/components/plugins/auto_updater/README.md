# Auto Updater Plugin

Checks whether a newer Consortium release is available and, if the user agrees, pulls
it and reinstalls dependencies in place.

- Label: `consortium.plugins.auto_updater_plugin`
- Autostart: yes (runs once during server startup)
- Enabled by default: no

## What it does

On `on_running` the plugin compares the release metadata published at
`data/release.json` on the project's `main` branch against
`services.release_service.release`. If the published release is newer it prints both
releases to the event log and prompts on the terminal:

```
Update the framework automatically? [y/N]:
```

Answering yes runs three blocking steps, in order:

1. `chdir` to `services.consortium_paths_service.consortium_root`
2. `git pull`
3. `uv sync`

Each subprocess is run synchronously behind a spinner. This deliberately blocks the
event loop so that nothing else starts up mid-update and so other components' log lines
do not interleave with the update output. On success the plugin asks you to restart the
server (CTRL-C) to actually apply the update; it never restarts the process itself.

Any failure (unreachable release file, non-JSON response, non-zero exit from `git pull`
or `uv sync`) is logged via `event_logger.failure` and the plugin returns without
changing anything further.

## Usage

Enable it in `manifest.json`:

```json
{
    "entry_point": "plugin:Plugin",
    "enabled": true
}
```

Then start the server from an interactive terminal. The prompt requires a TTY, so leave
this plugin disabled when the server runs detached or under a service manager. The
update itself requires the install to be a git checkout with `git` and `uv` on `PATH`.

## Notes

- The remote fetch in `on_running` is currently commented out and replaced by a
  hardcoded mock release (`Mock Release`, `v9.9.9`, released 2099), so the plugin will
  always report an available update. Restore the
  `await self._get_latest_release_json_data()` call to check the real release feed.
- `git pull` will fail on a dirty working tree or a checkout with local commits. Update
  manually in that case.
