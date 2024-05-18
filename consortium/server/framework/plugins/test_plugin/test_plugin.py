from consortium.server.framework.base_plugin import BasePlugin


class TestPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            name="Test Plugin",
            description="A plugin for testing purposes.",
            authors=["Consortium"],
            autostart=True,
        )

    async def on_plugin_started(self) -> None:
        pass

    async def on_plugin_running(self) -> None:
        pass

    async def on_plugin_stopped(self) -> None:
        pass

    async def on_plugin_cancelled(self) -> None:
        pass

    async def on_plugin_errored(self, exc: Exception) -> None:
        pass
