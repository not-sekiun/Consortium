from consortium.framework.plugins import BasePlugin


class Plugin(BasePlugin):
    label = "consortium.tests.services.mock_plugin_bad_version"
    name = "Mock Bad Version Plugin"
    description = "Plugin with a framework version specifier that won't match the running server."
    version = "0.1.0"
    compatible_framework_version = ">=999.0.0"
    authors = {"test"}
    autostart = False
