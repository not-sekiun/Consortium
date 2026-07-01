from consortium.framework.plugins import BasePlugin


class WrongName(BasePlugin):
    label = "consortium.tests.services.mock_plugin_bad_symbol"
    name = "Wrong Name Plugin"
    description = ""
    version = "0.1.0"
    authors = {"test"}
    autostart = False
