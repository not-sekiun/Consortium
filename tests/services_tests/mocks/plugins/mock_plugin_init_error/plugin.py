from consortium.framework.plugins import BasePlugin


class Plugin(BasePlugin):
    label = "consortium.tests.services.mock_plugin_init_error"
    name = "Mock Init Error Plugin"
    description = "Plugin whose __init__ raises to trigger InternalComponentProjectError."
    version = "0.1.0"
    authors = {"test"}
    autostart = False

    def __init__(self):
        raise RuntimeError("deliberate init-time error")
