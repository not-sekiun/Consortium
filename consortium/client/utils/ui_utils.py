import asyncio
from functools import wraps

from rich.live import Live
from rich.spinner import Spinner

from consortium.client.utils.printer_utils import console


# Currently only used for client session connection related functions
def with_spinner(text: str = "Connecting to server...", timeout: int = 10):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            spinner = Spinner("dots", text=f"{text} ({timeout}s)")

            async def countdown(live: Live) -> None:
                for remaining in range(timeout, 0, -1):
                    spinner.update(text=f"{text} ({remaining}s)")
                    live.update(spinner)
                    await asyncio.sleep(1)

            with Live(
                spinner, refresh_per_second=10, transient=True, console=console
            ) as live:
                countdown_task = asyncio.create_task(countdown(live))
                try:
                    return await func(*args, **kwargs)
                finally:
                    countdown_task.cancel()

        return wrapper

    return decorator
