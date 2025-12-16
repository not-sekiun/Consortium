import asyncio
from collections import namedtuple


async def run_command(*args, **kwargs) -> tuple:
    """
    Asynchronously run a command in a subprocess shell and return the stdout, stderr
    and return code.
    """
    process = await asyncio.create_subprocess_exec(*args, **kwargs)
    await process.wait()
    return namedtuple("CommandResult", ["stdout", "stderr", "return_code"])(
        process.stdout,
        process.stderr,
        process.returncode,
    )
