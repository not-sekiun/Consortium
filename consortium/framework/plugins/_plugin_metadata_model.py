import pydantic


class PluginMetadataModel(pydantic.BaseModel):
    label: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    compatible_framework_version: str | None = None
    authors: set[str] = set()
    autostart: bool = True
    plugin_dependencies: set[tuple[str, str]] = set()


try:
    PluginMetadataModel(
        label="Test Plugin",
        name="Test Plugin",
        description="A test plugin",
        version="1.0.0",
        compatible_framework_version="1.0.0",
        authors={"Author1", "Author2"},
        autostart=True,
        plugin_dependencies={("DependencyPlugin",)},
    )
    print("PluginMetadataModel is valid")
except pydantic.ValidationError as e:
    print(e.errors())
