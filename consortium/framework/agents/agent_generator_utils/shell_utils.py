import asyncio


async def run_command(*args, **kwargs) -> asyncio.subprocess.Process:
    """
    Asynchronously run a command in a subprocess and wait for it to complete.
    """
    process = await asyncio.create_subprocess_exec(*args, **kwargs)
    await process.wait()
    return process
