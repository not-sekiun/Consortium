import pathlib

import prompt_toolkit

PYPROJECT_TEMPLATE = """[project]
name = "consortium-plugin-{slugified_name}"
dependencies = []

[project.entry-points."consortium.plugins"]
{slugified_name} = "{plugin_module}:Plugin"
"""

PLUGIN_TEMPLATE = """from consortium.framework.plugins.base_plugin import BasePlugin


class Plugin(BasePlugin):
    label = "{plugin_label}"
    name = "{name}"

    async def on_started(self) -> None: ...

    async def on_running(self) -> None: ...

    async def on_stopped(self) -> None: ...

    async def on_completed(self) -> None: ...

    async def on_cancelled(self) -> None: ...

    async def on_errored(self, runtime_error: Exception) -> None: ...

"""

MANIFEST_TEMPLATE = """{
    entry_point: "{plugin_module}:Plugin}"
    enabled: true
}
"""


def to_snake_case(string: str) -> str:
    return string.replace("-", "_").replace(" ", "_").lower()


def to_slug_case(string: str) -> str:
    return string.replace("_", "-").replace(" ", "-").lower()


def main():
    session = prompt_toolkit.PromptSession()

    while True:
        plugin_label = session.prompt(
            "Plugin label (Must be unique across all installed plugins, recommended format: <author>.<label> all lowercase with snake_case formatting): ",
        )
        plugin_label = plugin_label.strip()
        if not plugin_label:
            print("Plugin label cannot be empty.")
            continue
        break

    # Compute derived names from the human-readable name
    while True:
        name = session.prompt(
            "Plugin name (Human-readable, recommended format: Use spaces to separate words, do not end the plugin name with 'Plugin' that will be automatically added): ",
        )
        name = name.strip()
        if not name:
            print("Plugin name cannot be empty.")
            continue
        plugin_directory = to_snake_case(name)
        plugin_module = to_snake_case(name) + "_plugin.py"
        slugified_name = to_slug_case(name)
        plugin_project_directory = pathlib.Path(
            "consortium",
            "components",
            "plugins",
            plugin_directory,
        )
        if plugin_project_directory.exists():
            print(
                f"Auto-generated plugin project directory filepath '{plugin_project_directory}' already exists. Specify a different name to prevent conflict.",
            )
            continue
        break

    plugin_project_directory.mkdir(parents=True)
    with open(plugin_project_directory / "__init__.py", "w") as f:
        f.write("")
    with open(plugin_project_directory / "pyproject.toml", "w") as f:
        f.write(
            PYPROJECT_TEMPLATE.format(
                slugified_name=slugified_name,
                plugin_module=plugin_module,
            ),
        )
    with open(plugin_project_directory / f"{plugin_module}", "w") as f:
        f.write(PLUGIN_TEMPLATE.format(plugin_label=plugin_label, name=name))

    print(f"Created plugin project directory at '{plugin_project_directory}'.")
    print(
        "Note: Add third-party dependencies within the project's `pyproject.toml` file.",
    )
    print("Next steps:")
    print(f"    cd {plugin_project_directory}")
    print("    poetry install .  # (optional, for development)")
    print("    # Start your Consortium server, the plugin will be auto-discovered\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPlugin project creation aborted.")
