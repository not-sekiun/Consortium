# Project Setup

This guide builds a complete plugin step by step. The plugin we will write is an
**Agent Report Plugin**: a background component that queries the framework every N
seconds for the current list of registered agents and logs a formatted summary. By the
time we reach [Complete Plugin Example](complete-plugin-example.md), it will demonstrate
every major plugin concept.

## Setting up the project files

Create a directory for the plugin under `consortium/components/plugins/`:

```
consortium/components/plugins/agent_report/
├── manifest.json
├── plugin.py
└── config.json
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

Continue to [Plugin Metadata](plugin-metadata.md) to declare the plugin class itself.
