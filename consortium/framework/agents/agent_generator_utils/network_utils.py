import asyncio
from functools import cache

import aiohttp

from consortium.framework.listeners.listener_utils.network_utils import get_local_ip

__all__ = [
    "get_local_ip",
    "get_remote_ip_async",
]  # Re-export the shared listener network utility function


async def get_remote_ip_async() -> str:
    """Resolve the host's public IP address asynchronously.

    Returns:
        The address reported by api.ipify.org, or ``127.0.0.1`` if the request cannot
        connect or times out.
    """
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        ) as session:
            async with session.get("https://api.ipify.org") as request:
                return await request.text()
    except aiohttp.ClientConnectorError, TimeoutError:
        return "127.0.0.1"


@cache
def get_remote_ip_sync() -> str:
    """Resolve and cache the host's public IP address synchronously.

    Returns:
        The address returned by get_remote_ip_async().
    """
    return asyncio.run(get_remote_ip_async())
