import asyncio


async def run_command(*args, **kwargs) -> asyncio.subprocess.Process:
    """Asynchronously run a command in a subprocess and wait for it to complete.

    A thin wrapper around asyncio.create_subprocess_exec that awaits the spawned
    process before returning it, so callers can inspect the completed process. All
    positional and keyword arguments are forwarded directly to create_subprocess_exec:
    positional arguments supply the program and its arguments (for example, "ls",
    "-la"), and keyword arguments supply options such as stdout, stderr, or cwd.

    Returns:
        The completed subprocess process, from which the return code and any
        captured output streams can be read.
    """
    process = await asyncio.create_subprocess_exec(*args, **kwargs)
    await process.wait()
    return process
