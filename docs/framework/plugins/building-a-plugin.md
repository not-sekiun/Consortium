# Building a Plugin

This guide builds a complete plugin step by step. The plugin we will write is an
**Agent Report Plugin**: a background component that queries the framework every N
seconds for the current list of registered agents and logs a formatted summary. By the
time we reach the complete version, it will demonstrate every major plugin concept.

## Setting up the project files

Create a directory for the plugin under `consortium/components/plugins/`:

```
consortium/components/plugins/agent_report/
    manifest.json
    plugin.py
    config.json
```

`manifest.json` points the component loader at the plugin class. The entry point format
is `<module>:<class>`. The class must be named `Plugin` by convention:

```json
{
    "entry_point": "plugin:Plugin",
    "enabled": true
}
```

`config.json` will hold the reporting interval (the plugin will load this at startup):

```json
{
    "interval_seconds": 30
}
```

## Step 1: The minimum viable plugin

A valid plugin requires at minimum a class that inherits from `BasePlugin` and declares
the required metadata attributes. All metadata is declared at class level and validated
at class definition time, so missing or malformed values raise errors at import rather
than at runtime.

```python
from consortium.framework.plugins import BasePlugin


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
```

### Metadata attributes

`label` is the stable, globally unique identifier for this plugin. It is used to
reference the plugin in persisted configuration and across server restarts. Choose a
reverse-DNS style string that is unique across your entire Consortium installation.

`compatible_framework_version` is a
[PEP 440 version specifier](https://peps.python.org/pep-0440/). The framework checks
this at load time and refuses to load a plugin whose specifier does not cover the running
framework version. Use `">=0.1.0"` for broad compatibility or pin tightly when your
plugin depends on a specific framework API.

## Step 2: on_started

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

### Signalling errors: PluginStartError

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
are `PluginRuntimeError` (from `on_running()`) and `PluginStopError` (from `on_stopped()`).

### self.environment

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

### self.plugin_project_folder

`self.plugin_project_folder` is a `pathlib.Path` pointing to the directory that contains
your plugin's source files. Use it to load sibling files without hard-coding absolute
paths:

```python
config_path = self.plugin_project_folder / "config.json"
data_path = self.plugin_project_folder / "session_data.json"
```

### self.logger

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

## Step 3: on_running and the async loop

`on_running()` is the plugin's main loop. The framework wraps it in an asyncio Task
immediately after `on_started()` returns. This Task runs concurrently with all other
server activity.

**`on_running()` must never block the event loop.** Calling `time.sleep()`, performing
synchronous network I/O, or any CPU-heavy loop without an `await` will stall the entire
server for the duration of that call. Every wait must yield control back to the event
loop with `await`.

### The stop_event pattern

`self.stop_event` is an `asyncio.Event` that the framework sets when `stop()` is called.
For a periodic loop, wait on the stop event with a timeout rather than using
`asyncio.sleep()`. This allows the plugin to respond immediately to a stop request
instead of sleeping through a full interval:

```python
async def on_running(self) -> None:
    while True:
        agents = self.services.agents_service.get_all_agents()
        self.logger.info(self._build_report(agents))
        self.environment.total_reports_emitted += 1

        try:
            await asyncio.wait_for(
                self.stop_event.wait(),
                timeout=self.environment.interval,
            )
            # stop_event was set: a stop was requested, exit the loop cleanly
            break
        except asyncio.TimeoutError:
            # The interval elapsed normally, continue to the next iteration
            pass
```

Contrast this with `asyncio.sleep()`, which would keep the plugin unresponsive to stop
requests for the full interval duration. The `stop_event.wait()` with timeout pattern is
the idiomatic choice for any periodic plugin.

For plugins that do not need a timer and simply need to stay alive until stopped (such as
`persistent_listeners` or `persistent_agent_generators`), the minimal form is:

```python
async def on_running(self) -> None:
    await self.stop_event.wait()
```

### Accessing services

`self.services` is a namespace that exposes every framework service as an attribute.
All service method calls are synchronous and return immediately:

```python
agents = self.services.agents_service.get_all_agents()
listeners = self.services.listeners_service.get_all_listeners()
generators = self.services.agent_generators_service.get_all_agent_generators()
```

Browse the available services in `consortium/server/services/`. Each file corresponds
to one service on the namespace (e.g. `agents_service.py` becomes
`self.services.agents_service`). The debug console plugin (`consortium/components/plugins/debug_console/`)
gives you live tab-completed access to every service at runtime.

## Step 4: on_stopped

`on_stopped()` is called when `stop()` is invoked from outside the plugin. The stop_event
is set before `on_stopped()` is called, so any `await self.stop_event.wait()` in the
running loop will have already unblocked. Use `on_stopped()` for final cleanup: flushing
buffers, closing connections, writing final state to disk.

```python
async def on_stopped(self) -> None:
    self.logger.info(
        "Agent Report Plugin stopped after {} report(s) emitted.",
        self.environment.total_reports_emitted,
    )
```

Raise `PluginStopError` if the stop cannot complete cleanly:

```python
async def on_stopped(self) -> None:
    try:
        self._flush_pending_data()
    except IOError as exc:
        raise PluginStopError(
            message=f"Failed to flush data on stop: {exc}",
        ) from exc
```

### on_completed

`on_completed()` fires when `on_running()` returns normally without `stop()` having been
called. This is the "ran to completion" path, as opposed to the "was stopped externally"
path. Most persistent background plugins never hit `on_completed()` because their loop
runs until `stop()` is called. A plugin like `auto_updater`, which performs a single
check and exits, uses `on_completed()` to handle the post-run cleanup.

For a plugin whose loop is guarded by `stop_event`, leave `on_completed()` as a no-op:

```python
async def on_completed(self) -> None:
    pass
```

## Step 5: Error handling

### PluginRuntimeError and on_errored

Raising `PluginRuntimeError` from `on_running()` signals a recoverable runtime failure.
The framework transitions the plugin to `ERRORED`, calls `on_errored()`, and ends the
main Task. The server keeps running.

```python
from consortium.framework.exceptions.plugins_framework_exceptions import PluginRuntimeError

async def on_running(self) -> None:
    while True:
        try:
            agents = self.services.agents_service.get_all_agents()
        except Exception as exc:
            raise PluginRuntimeError(
                message=f"Failed to query agents service: {exc}",
                detail={"exception_type": type(exc).__name__},
            ) from exc

        self.logger.info(self._build_report(agents))
        ...

async def on_errored(self, error) -> None:
    # The default implementation logs the error at the error level.
    # Override to add alerting, restart logic, or other custom handling.
    self.logger.error("Plugin error: {}", error.message)
```

`detail` is an optional dict that can carry structured diagnostic data. It is attached
to the error object and surfaced by the framework's logging.

The distinction between `PluginRuntimeError` and unhandled exceptions is important.
Unhandled exceptions (anything that is not a `PluginRuntimeError`) transition the plugin
directly to `FATAL` and call `on_fatal()` instead. Use `PluginRuntimeError` for errors
you anticipate and want handled gracefully; let truly unexpected exceptions bubble up as
fatal so they are clearly distinguished in logs.

### on_fatal and ComponentLifeCycleFatalContext

Any unhandled exception that escapes `on_running()`, `on_started()`, `on_stopped()`, or
`on_cancelled()` calls `on_fatal()`. The `fatal_context` argument identifies which
lifecycle phase the exception came from:

```python
from consortium.framework._components import ComponentLifeCycleFatalContext

async def on_fatal(self, exc: Exception, fatal_context: ComponentLifeCycleFatalContext) -> None:
    # The default logs the full traceback. Override to add a monitoring webhook
    # call, send an alert, or attempt some form of recovery.
    self.logger.error(
        "Fatal error during {}: {}: {}",
        fatal_context,
        type(exc).__name__,
        exc,
    )
```

The values of `ComponentLifeCycleFatalContext` are `START`, `RUNNING`, `STOP`,
`CANCEL`, and `ERROR` (fatal during `on_errored`). The `persistent_listeners` plugin
delegates entirely to the default `on_fatal` implementation from `BasePlugin`, which
logs the full traceback. Override it only when you need behaviour beyond logging.

## Step 6: Private helpers and self conventions

### Private methods

Underscore-prefixed methods are private: they are internal helpers that are not intended
to be called from outside the class. Public methods have no prefix and form the plugin's
intended interface.

```python
async def on_running(self) -> None:
    while True:
        agents = self.services.agents_service.get_all_agents()
        # _build_report is private: internal to this class
        self.logger.info(self._build_report(agents))
        ...

def _build_report(self, agents: list) -> str:
    # Private helper: formats agent data for the log line
    if not agents:
        return "No agents currently registered."
    lines = [f"Registered agents ({len(agents)}):"]
    for agent in agents:
        lines.append(f"  - {agent.name}")
    return "\n".join(lines)
```

Helpers that do not need access to `self` should be `@staticmethod`:

```python
@staticmethod
def _format_agent_line(agent) -> str:
    return f"  [{agent.agent_id}] {agent.name}"
```

### What lives on self

Every plugin instance has these attributes:

| Attribute | Type | Description |
|---|---|---|
| `self.plugin_id` | `uuid.UUID` | Unique identifier for this plugin instance |
| `self.name` | `str` | Display name from the class attribute |
| `self.label` | `str` | Stable label from the class attribute |
| `self.description` | `str` | Description from the class attribute |
| `self.version` | `Version` | Parsed version from the `version` class attribute |
| `self.autostart` | `bool` | Whether this plugin starts with the server |
| `self.status` | `Status` | Current lifecycle status, with `.state` for the state string |
| `self.stop_event` | `asyncio.Event` | Set when `stop()` is called |
| `self.environment` | `SimpleNamespace` | Mutable runtime state namespace |
| `self.services` | `SimpleNamespace` | Framework services namespace |
| `self.logger` | `loguru.Logger` | Plugin-scoped logger |
| `self.plugin_project_folder` | `pathlib.Path` | Path to this plugin's source directory |

Do not set attributes directly on `self` for runtime state. Use `self.environment`
instead. Framework-managed attributes like `self.stop_event` and `self.status` should
be read but not replaced.

## Complete plugin

Here is the complete Agent Report Plugin combining all of the above:

```python
import asyncio
import json

from consortium.framework.plugins import BasePlugin
from consortium.framework.exceptions.plugins_framework_exceptions import (
    PluginRuntimeError,
    PluginStartError,
)


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
            "Started. Reporting every {} seconds.",
            self.environment.interval,
        )

    async def on_running(self) -> None:
        while True:
            try:
                agents = self.services.agents_service.get_all_agents()
            except Exception as exc:
                raise PluginRuntimeError(
                    message=f"Failed to query agents service: {exc}",
                    detail={"exception_type": type(exc).__name__},
                ) from exc

            self.logger.info(self._build_report(agents))
            self.environment.total_reports_emitted += 1

            try:
                await asyncio.wait_for(
                    self.stop_event.wait(),
                    timeout=self.environment.interval,
                )
                break
            except asyncio.TimeoutError:
                pass

    async def on_stopped(self) -> None:
        self.logger.info(
            "Stopped after {} report(s) emitted.",
            self.environment.total_reports_emitted,
        )

    async def on_completed(self) -> None:
        pass

    async def on_cancelled(self) -> None:
        pass

    async def on_errored(self, error: PluginRuntimeError) -> None:
        self.logger.error("Runtime error: {}", error.message)

    def _build_report(self, agents: list) -> str:
        if not agents:
            return "No agents currently registered."
        lines = [f"Registered agents ({len(agents)}):"]
        for agent in agents:
            lines.append(f"  - {agent.name}")
        return "\n".join(lines)
```

Companion `config.json`:

```json
{
    "interval_seconds": 30
}
```

## Further examples

The built-in plugins in `consortium/components/plugins/` cover the full range of plugin
patterns:

- `persistent_listeners/plugin.py` - loads JSON state in `on_started`, blocks on
  `stop_event` in `on_running`, and serialises live state in `on_stopped`. The canonical
  example of a plugin that bridges server restarts.

- `persistent_agent_generators/plugin.py` - the same pattern applied to agent generators.

- `debug_console/plugin.py` - uses `on_started` to configure logging, then runs an
  interactive prompt loop in `on_running`. Demonstrates blocking with a prompt rather
  than a timer, and shows how `self.services` can be passed into user-facing tools.

- `auto_updater/plugin.py` - performs a one-shot network check in `on_running` and
  returns, hitting `on_completed`. Demonstrates plugins with no persistent loop and
  shows how to intentionally block the event loop when sequencing is critical (the
  comment in that file explains the tradeoff explicitly).
