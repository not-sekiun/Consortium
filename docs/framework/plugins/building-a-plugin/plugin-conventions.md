# Plugin Conventions

## Private methods

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

## What lives on self

Every plugin instance has these attributes:

| Attribute                    | Type              | Description                                                  |
|------------------------------|-------------------|--------------------------------------------------------------|
| `self.plugin_id`             | `uuid.UUID`       | Unique identifier for this plugin instance                   |
| `self.name`                  | `str`             | Display name from the class attribute                        |
| `self.label`                 | `str`             | Stable label from the class attribute                        |
| `self.description`           | `str`             | Description from the class attribute                         |
| `self.version`               | `Version`         | Parsed version from the `version` class attribute            |
| `self.autostart`             | `bool`            | Whether this plugin starts with the server                   |
| `self.status`                | `Status`          | Current lifecycle status, with `.state` for the state string |
| `self.stop_event`            | `asyncio.Event`   | Set when `stop()` is called                                  |
| `self.environment`           | `SimpleNamespace` | Mutable runtime state namespace                              |
| `self.services`              | `SimpleNamespace` | Framework services namespace                                 |
| `self.logger`                | `loguru.Logger`   | Plugin-scoped logger                                         |
| `self.root_directory`        | `pathlib.Path`    | Path to this plugin's source directory                       |

Do not set attributes directly on `self` for runtime state. Use `self.environment`
instead. Framework-managed attributes like `self.stop_event` and `self.status` should
be read but not replaced.

See the [Complete Plugin Example](complete-plugin-example.md) for all of these concepts
combined into one plugin.
