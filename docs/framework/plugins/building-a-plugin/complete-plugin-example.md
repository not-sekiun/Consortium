# Complete Plugin Example

Here is the complete Agent Report Plugin combining all of the concepts covered in
[Project Setup](project-setup.md) through [Plugin Conventions](plugin-conventions.md):

```python
import asyncio
import json

from consortium.framework.plugins import BasePlugin
from consortium.framework.signal_exceptions.plugins_signal_exceptions import (
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
    config_path = self.root_directory / "config.json"
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

- `persistent_agent_generators/plugin.py` - the same pattern applied to agent
  generators.

- `debug_console/plugin.py` - uses `on_started` to configure logging, then runs an
  interactive prompt loop in `on_running`. Demonstrates blocking with a prompt rather
  than a timer, and shows how `self.services` can be passed into user-facing tools.

- `auto_updater/plugin.py` - performs a one-shot network check in `on_running` and
  returns, hitting `on_completed`. Demonstrates plugins with no persistent loop and
  shows how to intentionally block the event loop when sequencing is critical (the
  comment in that file explains the tradeoff explicitly).
