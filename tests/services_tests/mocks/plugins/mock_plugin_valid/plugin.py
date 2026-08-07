from consortium.framework.plugins import BasePlugin


class Plugin(BasePlugin):
    label = "consortium.tests.services.mock_plugin_valid"
    name = "Mock Valid Plugin"
    description = "Valid no-op plugin for service loader tests."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"test"}
    autostart = False
