import asyncio
import pathlib
from collections.abc import AsyncGenerator
from dataclasses import dataclass


class AsyncProcess:
    """Asynchronous subprocess wrapper with buffered and streaming execution modes.

    Attributes:
        args: Positional arguments passed to asyncio.create_subprocess_exec().
        kwargs: Keyword arguments passed to asyncio.create_subprocess_exec().
        return_code: Exit status from the most recently completed process, or None
            before completion.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.return_code: int | None = None

    async def execute(
        self, working_dir: str | pathlib.Path | None = None
    ) -> tuple[str, str]:
        """Run the process and return its buffered standard output and error streams.

        Args:
            working_dir: Directory in which to execute the process. Applied to the
                spawned process alone, leaving the caller's working directory untouched.

        Returns:
            A tuple containing stripped standard output and standard error text.
        """
        # The working directory is handed to the child process rather than applied
        # with `os.chdir`. The interpreter has a single working directory shared by
        # every coroutine, so changing it here would leak into any concurrently
        # running task and be restored out from under processes that are still
        # spawning.
        process = await asyncio.create_subprocess_exec(
            *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
            **self.kwargs,
        )
        stdout, stderr = await process.communicate()
        self.return_code = await process.wait()

        return stdout.decode().rstrip(), stderr.decode().rstrip()

    async def stream(
        self, working_dir: str | pathlib.Path | None = None
    ) -> AsyncGenerator[str]:
        """Run the process and yield combined standard output and error lines.

        Args:
            working_dir: Directory in which to execute the process. Applied to the
                spawned process alone, leaving the caller's working directory untouched.

        Yields:
            Each output line with trailing newline characters removed.
        """
        # See `execute` for why the working directory is passed to the child process
        # instead of being applied with `os.chdir`.
        process = await asyncio.create_subprocess_exec(
            *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Redirect stderr into stdout so we stream both together
            cwd=working_dir,
            **self.kwargs,
        )

        # `stdout` is only ever `None` when the process was spawned without a pipe for
        # it, which cannot happen here because we always request one above.
        assert process.stdout is not None

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
    """Buffered output produced by an asynchronous process.

    Attributes:
        return_code: Exit status returned by the process.
        stdout: Standard output emitted by the process.
        stderr: Standard error emitted by the process.
    """

    return_code: int
    stdout: str
    stderr: str


async def run_command(
    *args, working_dir: str | pathlib.Path | None = None, **kwargs
) -> AsyncProcessOutput:
    """Run a command and return its buffered output.

    Args:
        *args: Positional arguments passed to asyncio.create_subprocess_exec().
        working_dir: Directory in which to execute the command.
        **kwargs: Keyword arguments passed to asyncio.create_subprocess_exec().

    Returns:
        The completed process's exit status, standard output, and standard error.
    """
    async_process = AsyncProcess(*args, **kwargs)
    stdout, stderr = await async_process.execute(working_dir=working_dir)
    return AsyncProcessOutput(
        return_code=async_process.return_code
        if async_process.return_code is not None
        else 0,
        stdout=stdout,
        stderr=stderr,
    )


def run_and_stream_command(
    *args, working_dir: str | pathlib.Path | None = None, **kwargs
) -> AsyncGenerator[str]:
    """Run a command and return an asynchronous iterator over its combined output.

    Args:
        *args: Positional arguments passed to asyncio.create_subprocess_exec().
        working_dir: Directory in which to execute the command.
        **kwargs: Keyword arguments passed to asyncio.create_subprocess_exec().

    Returns:
        An asynchronous generator that yields output lines as they are produced.
    """
    return AsyncProcess(*args, **kwargs).stream(working_dir=working_dir)
