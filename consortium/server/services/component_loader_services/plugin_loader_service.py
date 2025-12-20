from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions import (
    PluginsFrameworkError,
)
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
)


class PluginLoaderService(ComponentLoaderService[BasePlugin]):
    _component_type = BasePlugin
    _component_framework_error = PluginsFrameworkError
    _manifest_json_schema = {
        "type": "object",
        "properties": {
            "entry_point": {"type": "string"},
            "enabled": {"type": "boolean"},
        },
        "required": ["entry_point", "enabled"],
        "additionalProperties": False,
    }
