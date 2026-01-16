import asyncio

from pydantic import BaseModel


class TimeoutCapabilityConfig(BaseModel):
    default_value: int | float


class TimeoutCapability:
    timeout_capability_config: TimeoutCapabilityConfig

    async def apply_timeout(
        self,
        coro: callable,
        timeout_seconds: float | None = None,
        *args,
        **kwargs,
    ):
        """
        Apply a timeout to an asynchronous operation.

        Args:
            coro (callable): The coroutine function to execute.
            timeout_seconds (float): The maximum time to wait for the operation to
                complete.
            *args: Positional arguments to pass to the coroutine.
            **kwargs: Keyword arguments to pass to the coroutine.

        Returns:
            The result of the coroutine if it completes within the timeout period.

        Raises:
            asyncio.TimeoutError: If the operation exceeds the specified timeout.
        """
        if timeout_seconds is None:
            timeout_seconds = self.timeout_capability_config.default_value

        return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout_seconds)
