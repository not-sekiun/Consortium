from consortium.framework.plugins import BasePlugin


class Plugin(BasePlugin):
    label = "consortium.tests.services.mock_plugin_disabled"
    name = "Mock Disabled Plugin"
    description = "Disabled plugin for loader tests."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"test"}
    autostart = False
