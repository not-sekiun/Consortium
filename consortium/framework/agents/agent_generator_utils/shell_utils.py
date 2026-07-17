import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass


class AsyncProcess:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.return_code: int | None = None

    async def execute(self) -> tuple[str, str]:
        process = await asyncio.create_subprocess_exec(
            *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **self.kwargs,
        )
        stdout, stderr = await process.communicate()
        self.return_code = await process.wait()
        return stdout.decode().rstrip(), stderr.decode().rstrip()

    async def stream(self) -> AsyncGenerator[str]:
        process = await asyncio.create_subprocess_exec(
            *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Redirect stderr into stdout so we stream both together
            **self.kwargs,
        )

        # Read output line-by-line as it comes in
        while True:
            line = await process.stdout.readline()
            if not line:
                break  # No more output, process has finished

            yield line.decode().rstrip()  # Remove newline characters

        # Wait for the process to fully exit and get the return code
        self.return_code = await process.wait()


@dataclass(frozen=True)
class AsyncProcessOutput:
    return_code: int
    stdout: str
    stderr: str


async def run_command(*args, **kwargs) -> AsyncProcessOutput:
    async_process = AsyncProcess(*args, **kwargs)
    stdout, stderr = await async_process.execute()
    return AsyncProcessOutput(
        return_code=async_process.return_code
        if async_process.return_code is not None
        else 0,
        stdout=stdout,
        stderr=stderr,
    )


def run_and_stream_command(*args, **kwargs) -> AsyncGenerator[str]:
    return AsyncProcess(*args, **kwargs).stream()
