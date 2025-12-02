from pydantic import BaseModel


class PluginMetadataModel(BaseModel):
    label: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    compatible_framework_version: str | None = None
    authors: set[str] = set()
    autostart: bool = True
    plugin_dependencies: set[str] = set()
