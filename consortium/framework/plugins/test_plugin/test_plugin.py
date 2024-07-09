import asyncio

from rich.progress import track
from rich.table import Table

from consortium.framework.base_plugin import BasePlugin


class TestPlugin(BasePlugin):
    name = "Test Plugin"

    async def on_plugin_started(self) -> None:
        pass

    async def on_plugin_running(self) -> None:
        listener_profiles_service = self.server_services.listener_profiles_service
        http_listener_profile = listener_profiles_service.get_all_listener_profiles()[0]
        http_listener = http_listener_profile.listener
        http_listener_instance = http_listener(
            name="HTTP Listener",
            description="A simple HTTP listener",
            parameters={"local_host": "127.0.0.1", "local_port": 8080},
        )
        try:
            await http_listener_instance.start_listener()
        except Exception:
            pass
        print(http_listener_instance.status)

    async def on_plugin_stopped(self) -> None:
        pass

    async def on_plugin_cancelled(self) -> None:
        pass

    async def on_plugin_errored(self, exc: Exception) -> None:
        pass
