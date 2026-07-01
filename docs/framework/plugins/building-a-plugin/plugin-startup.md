# Plugin Startup

`on_started()` is called once immediately after the status transitions to `STARTED`,
before the main loop Task is scheduled. This is where you perform one-time setup: loading
configuration files, opening connections, and initialising state in `self.environment`.

```python
import asyncio
import json

from consortium.framework.plugins import BasePlugin
from consortium.framework.exceptions.plugins_framework_exceptions import PluginStartError


class Plugin(BasePlugin):
    label = "consortium.plugins.agent_report"
    name = "Agent Report Plugin"
    description = (
        "Logs a periodic summary of all currently registered agents "
        "at a configurable interval."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Your Name"}
    autostart = True

    async def on_started(self) -> None:
        config_path = self.plugin_project_folder / "config.json"
        if not config_path.exists():
            raise PluginStartError(
                message=(
                    f"Configuration file not found at '{config_path}'. "
                    "Create a config.json with an 'interval_seconds' key."
                ),
            )
        with config_path.open("r") as f:
            config = json.load(f)

        self.environment.interval = config.get("interval_seconds", 60)
        self.environment.total_reports_emitted = 0
        self.logger.info(
            "Agent Report Plugin started. Reporting every {} seconds.",
            self.environment.interval,
        )
```

## Signalling errors: PluginStartError

The framework uses exceptions to communicate from hook methods back to the lifecycle
engine. Raising `PluginStartError` from `on_started()` aborts the start sequence cleanly:
the plugin's status reverts to `INITIALIZED` and the error is surfaced to whoever called
`start()`. This is the correct way to signal that a plugin cannot start.

```python
# Correct: tells the lifecycle engine to abort startup cleanly
raise PluginStartError(message="Configuration file missing.")

# Incorrect: an unhandled exception transitions the plugin to FATAL
raise FileNotFoundError("config.json not found")
```

Only raise `PluginStartError` from `on_started()`. Its counterparts for the other phases
are `PluginRuntimeError` (from `on_running()`, see
[Plugin Error Handling](plugin-error-handling.md)) and `PluginStopError` (from
`on_stopped()`, see [Plugin Shutdown](plugin-shutdown.md)).

## self.environment

`self.environment` is a `types.SimpleNamespace` that is created fresh each time the
plugin is instantiated. Use it to carry mutable state across hook method calls:

```python
# Setting state in on_started
self.environment.interval = 30
self.environment.total_reports = 0

# Reading it later in on_running or on_stopped
if self.environment.total_reports > 0:
    ...
```

Do not store state as direct instance attributes (`self.interval = 30`). Using
`self.environment` keeps runtime state clearly separate from class-level configuration
and from the framework-managed attributes on `self`.

## self.plugin_project_folder

`self.plugin_project_folder` is a `pathlib.Path` pointing to the directory that contains
your plugin's source files. Use it to load sibling files without hard-coding absolute
paths:

```python
config_path = self.plugin_project_folder / "config.json"
data_path = self.plugin_project_folder / "session_data.json"
```

## self.logger

`self.logger` is a [loguru](https://github.com/Delgan/loguru) logger automatically bound
with the plugin's name and ID. Use `{}` placeholders rather than f-strings so loguru can
defer evaluation until the message is actually written:

```python
# Preferred: deferred evaluation
self.logger.info("Found {} agents.", len(agents))

# Avoid: eagerly evaluated even if the log level is filtered out
self.logger.info(f"Found {len(agents)} agents.")
```

Available levels: `debug`, `info`, `success`, `warning`, `error`, `critical`.

Continue to [Plugin Running Loop](plugin-running-loop.md) to build the main loop.
