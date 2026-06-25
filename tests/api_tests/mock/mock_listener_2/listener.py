from consortium.framework.listeners import BaseListener


class Listener(BaseListener):
    async def on_started(self) -> None:
        pass

    async def on_running(self) -> None:
        await self.stop_event.wait()

    async def on_stopped(self) -> None:
        pass

    async def on_cancelled(self) -> None:
        pass
