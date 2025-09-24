import asyncio

from consortium.framework.plugins import BasePlugin


class MyAwesomePlugin(BasePlugin):
    label = "My Awesome Plugin"
    name = "My Awesome Plugin"
    description = "This is my awesome plugin."
    version = "1.0.0"
    compatible_framework_version = ">=1.0.0"
    authors = {"John Doe", "Jane Smith"}
    autostart = True
    plugin_dependencies = {("DependencyPlugin", ">=1.0.0")}

    async def on_started(self) -> None:
        print(f"{self.name} has started.")

    async def on_running(self) -> None:
        while not self.stop_event.is_set():
            print(self.server_services)
            await asyncio.sleep(1)

    async def on_completed(self) -> None:
        print(f"{self.name} has completed its task.")

    async def on_stopped(self) -> None:
        print(f"{self.name} has been stopped.")

    async def on_cancelled(self) -> None:
        print(f"{self.name} has been cancelled.")

    async def on_errored(self, exc: Exception) -> None:
        print(f"{self.name} encountered an error: {exc}")


async def main():
    plugin = MyAwesomePlugin()
    try:
        await plugin.start()
        await asyncio.sleep(3)  # Simulate some running time
        print(plugin.to_json())
        await plugin.stop()
        await asyncio.sleep(1)
        print(plugin.to_json())
    except Exception as exc:
        print(f"Exception occurred: {exc}")
        print(plugin.to_json())


if __name__ == "__main__":
    asyncio.run(main())
