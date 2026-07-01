# Plugin Metadata

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

## Metadata attributes

`label` is the stable, globally unique identifier for this plugin. It is used to
reference the plugin in persisted configuration and across server restarts. Choose a
reverse-DNS style string that is unique across your entire Consortium installation.

`compatible_framework_version` is a
[PEP 440 version specifier](https://peps.python.org/pep-0440/). The framework checks
this at load time and refuses to load a plugin whose specifier does not cover the running
framework version. Use `">=0.1.0"` for broad compatibility or pin tightly when your
plugin depends on a specific framework API.

Continue to [Plugin Startup](plugin-startup.md) to add one-time setup logic.
