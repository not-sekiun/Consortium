#!/usr/bin/env python3
"""
Drive the Consortium prompt-toolkit client without a Windows console buffer.

Run this tool through uv so it uses the project's client environment:

    uv run python tools/headless_client_driver.py -c help -c "session info"
    Get-Content commands.txt | uv run python tools/headless_client_driver.py
    uv run python tools/headless_client_driver.py --commands-file commands.txt

Arguments after ``--`` are forwarded to ``consortium.py client``:

    uv run python tools/headless_client_driver.py -c help -- --debug

The driver invokes the real ``consortium.py client`` entry point in-process. It
only replaces prompt-toolkit's input and output with its supported pipe-input
and plain-text implementations. Commands are newline-delimited. An ``exit``
command is appended at end-of-input unless ``--no-auto-exit`` is supplied.

Commands are submitted one at a time behind a readiness handshake rather than on
a fixed timer: before each submission the driver waits for the client to produce
output and then fall silent for ``--settle`` seconds, which is what stops a
command being queued while the previous one is still rendering. A command that
blocks silently for longer than ``--settle`` can still be raced, so ``--delay``
remains available as an additional per-command pause. ``--no-wait-for-ready``
restores the old purely time-based feeding.

The driver exits with the client's exit code. If the client exits before every
command has been submitted, the driver reports the dropped commands on stderr
and exits with code 3 (unless the client itself already failed).
"""

import argparse
import os
import runpy
import sys
import threading
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, TextIO

from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.data_structures import Size
from prompt_toolkit.input.base import PipeInput
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.plain_text import PlainTextOutput

# How long to wait for the feeder thread to drain its command source once the
# client has returned. The wait happens while the pipe input is still open so a
# feeder that is only slightly behind still delivers everything.
FEEDER_JOIN_TIMEOUT = 5.0

# Reported when commands were dropped but the client itself exited cleanly, so
# a delivery problem is not mistaken for a successful run.
DELIVERY_FAILURE_EXIT_CODE = 3

# How often the feeder rechecks the output stream while waiting for the client to
# become ready. Short enough that the handshake does not itself become the thing
# that paces the run.
READINESS_POLL_INTERVAL = 0.01


class HeadlessOutput(PlainTextOutput):
    def __init__(self, stdout: TextIO, columns: int, rows: int) -> None:
        super().__init__(stdout=stdout)
        self._size = Size(rows=rows, columns=columns)

    def get_size(self) -> Size:
        return self._size


# prompt-toolkit's flush_stdout() writes through `stdout.buffer` in binary whenever the
# stream exposes one, bypassing the text-mode write(). Wrapping the buffer keeps that
# path visible to the tracker, rather than hiding `buffer` to force writes back onto the
# text path and changing how the client's output is encoded.
class _TrackedBinaryStream:
    def __init__(self, buffer: Any, record_write: Callable[[], None]) -> None:
        self._buffer = buffer
        self._record_write = record_write

    def __getattr__(self, name: str) -> Any:
        return getattr(self._buffer, name)

    def write(self, data: bytes) -> int:
        written = self._buffer.write(data)
        if data:
            self._record_write()
        return written

    def flush(self) -> None:
        self._buffer.flush()


# Wraps the driver's stdout so the feeder thread can tell when the client has gone
# quiet. Both prompt-toolkit's rendering and the client's own direct writes pass
# through here: prompt-toolkit renders into the stream this wraps, and command output
# runs outside the interpreter's patch_stdout block so it reaches the same stream.
# That makes "no writes for a while" a usable proxy for "the REPL is back at its
# prompt", which a fixed sleep cannot approximate.
class _OutputActivityTracker:
    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._lock = threading.Lock()
        self._write_count = 0
        self._last_write_at = time.monotonic()
        self._buffer = (
            _TrackedBinaryStream(
                buffer=stream.buffer,
                record_write=self._record_write,
            )
            if hasattr(stream, "buffer")
            else None
        )

    # Delegate everything else the Output implementation reaches for (encoding, fileno,
    # isatty, and so on) to the wrapped stream.
    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)

    @property
    def buffer(self) -> _TrackedBinaryStream:
        # Report the same absence as the wrapped stream when it has no buffer, so
        # flush_stdout()'s hasattr() check still resolves correctly.
        if self._buffer is None:
            raise AttributeError("buffer")
        return self._buffer

    def _record_write(self) -> None:
        with self._lock:
            self._write_count += 1
            self._last_write_at = time.monotonic()

    def write(self, data: str) -> int:
        written = self._stream.write(data)
        if data:
            self._record_write()
        return written

    def flush(self) -> None:
        self._stream.flush()

    def snapshot(self) -> tuple[int, float]:
        with self._lock:
            return self._write_count, self._last_write_at

    @property
    def write_count(self) -> int:
        with self._lock:
            return self._write_count


class _ClientExited(Exception):
    # Raised inside the feeder once the client has returned, so the feed loop stops
    # without marking delivery complete. Reaching the end of the loop is what reports
    # a fully delivered run, and commands written into a pipe the client is no longer
    # reading have not been delivered in any useful sense.
    pass


def _wait_until_client_is_ready(
    tracker: _OutputActivityTracker,
    baseline_write_count: int,
    settle: float,
    timeout: float,
    client_exited: threading.Event,
) -> bool:
    # Ready means the client has written something since the previous command was
    # submitted and has then produced nothing for `settle` seconds. Requiring new
    # output matters as much as requiring silence: a stream that has been quiet since
    # before the command was sent has not yet started responding to it.
    deadline = time.monotonic() + timeout
    while True:
        # A client that has exited produces no further output, so without this the
        # wait could only ever end by running out the full timeout.
        if client_exited.is_set():
            return False
        write_count, last_write_at = tracker.snapshot()
        now = time.monotonic()
        if write_count > baseline_write_count and (now - last_write_at) >= settle:
            return True
        if now >= deadline:
            return False
        time.sleep(READINESS_POLL_INTERVAL)


def _configure_utf8_output() -> None:
    os.environ["PYTHONUTF8"] = "1"
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _read_command_file(path: Path) -> list[str]:
    commands = []
    with path.open(encoding="utf-8") as command_file:
        for raw_line in command_file:
            command = raw_line.rstrip("\r\n")
            if command.strip() and not command.lstrip().startswith("#"):
                commands.append(command)
    return commands


def _stdin_commands() -> Iterable[str]:
    for raw_line in sys.stdin:
        yield raw_line.rstrip("\r\n")


def _feed_commands(
    pipe_input: PipeInput,
    commands: Iterable[str],
    delay: float,
    auto_exit: bool,
    delivered: threading.Event,
    tracker: _OutputActivityTracker | None,
    settle: float,
    ready_timeout: float,
    client_exited: threading.Event,
) -> None:
    # Output volume as of the previous submission, so the readiness check can tell
    # output produced in response to that command apart from output that predates it.
    baseline_write_count = 0
    last_command = None

    def submit(command: str) -> None:
        nonlocal baseline_write_count

        if client_exited.is_set():
            raise _ClientExited

        if tracker is not None:
            if not _wait_until_client_is_ready(
                tracker=tracker,
                baseline_write_count=baseline_write_count,
                settle=settle,
                timeout=ready_timeout,
                client_exited=client_exited,
            ):
                # A wait cut short by the client exiting is not a settle failure, and
                # the undelivered commands are reported by the caller instead.
                if client_exited.is_set():
                    raise _ClientExited
                print(
                    f"headless driver: the client did not settle within "
                    f"{ready_timeout:g}s before '{command}'; the transcript around "
                    f"this command may be interleaved",
                    file=sys.stderr,
                )

        pipe_input.send_text(f"{command}\n")

        # Snapshot after submitting so the command's own echo counts as new output
        # for the next readiness check rather than satisfying it in advance.
        if tracker is not None:
            baseline_write_count = tracker.write_count
        if delay:
            time.sleep(delay)

    try:
        for command in commands:
            if not command.strip():
                continue
            submit(command)
            last_command = command.strip()

        if auto_exit and last_command != "exit":
            submit("exit")
    except (_ClientExited, EOFError, OSError):
        # The client may exit before all queued commands are consumed, either by
        # tearing down the pipe under the feeder or by returning while the feeder is
        # still working. The caller detects both through the unset delivered event.
        return
    delivered.set()


def _delivery_exit_code(
    feeder: threading.Thread,
    delivered: threading.Event,
    client_exit_code: int,
) -> int:
    if delivered.is_set():
        return client_exit_code

    if feeder.is_alive():
        reason = (
            "the command feeder did not finish within "
            f"{FEEDER_JOIN_TIMEOUT:g}s of the client exiting"
        )
    else:
        reason = "the client stopped reading before the command feeder finished"
    print(
        f"headless driver: {reason}; some commands were not delivered",
        file=sys.stderr,
    )
    return client_exit_code or DELIVERY_FAILURE_EXIT_CODE


def _system_exit_code(exc: SystemExit) -> int:
    if exc.code is None:
        return 0
    if isinstance(exc.code, int):
        return exc.code
    print(exc.code, file=sys.stderr)
    return 1


def _run_client(
    entrypoint: Path,
    client_args: list[str],
    commands: Iterable[str],
    columns: int,
    rows: int,
    delay: float,
    auto_exit: bool,
    settle: float,
    ready_timeout: float,
    wait_for_ready: bool,
) -> int:
    original_argv = sys.argv
    original_cwd = Path.cwd()
    original_sys_path = list(sys.path)
    original_stdout = sys.stdout
    tracker = _OutputActivityTracker(stream=sys.stdout) if wait_for_ready else None
    output = HeadlessOutput(
        stdout=sys.stdout if tracker is None else tracker,
        columns=columns,
        rows=rows,
    )

    try:
        os.chdir(entrypoint.parent)
        sys.path.insert(0, str(entrypoint.parent))
        sys.argv = [str(entrypoint), "client", *client_args]
        # Route the client's own writes through the tracker too. Command output is
        # produced outside the interpreter's patch_stdout block, so it would not be
        # observed through prompt-toolkit's output alone.
        if tracker is not None:
            sys.stdout = tracker
        client_exit_code = 0
        with create_pipe_input() as pipe_input:
            delivered = threading.Event()
            client_exited = threading.Event()
            feeder = threading.Thread(
                target=_feed_commands,
                args=(
                    pipe_input,
                    commands,
                    delay,
                    auto_exit,
                    delivered,
                    tracker,
                    settle,
                    ready_timeout,
                    client_exited,
                ),
                daemon=True,
                name="consortium-headless-client-input",
            )
            feeder.start()
            try:
                with create_app_session(input=pipe_input, output=output):
                    try:
                        runpy.run_path(str(entrypoint), run_name="__main__")
                    except SystemExit as exc:
                        client_exit_code = _system_exit_code(exc)
            finally:
                # Tell the feeder the client is gone before joining. Without this a
                # feeder parked in its readiness wait would sit out the whole join,
                # since an exited client never produces the output that wait needs.
                # Nothing submitted from here on would be executed anyway: the client
                # has stopped reading, so those commands are dropped, not delivered.
                client_exited.set()
                # Join inside the pipe input context so the feeder is never mid-send
                # when the pipe closes, and so `is_alive()` below distinguishes a
                # feeder that stopped from one that is stuck on its command source.
                feeder.join(FEEDER_JOIN_TIMEOUT)
        return _delivery_exit_code(feeder, delivered, client_exit_code)
    except KeyboardInterrupt:
        return 130
    finally:
        sys.argv = original_argv
        sys.path[:] = original_sys_path
        sys.stdout = original_stdout
        os.chdir(original_cwd)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Drive the Consortium client through prompt-toolkit pipe input.",
    )
    parser.add_argument(
        "-c",
        "--command",
        action="append",
        default=[],
        help="Client command to run. May be supplied more than once.",
    )
    parser.add_argument(
        "-f",
        "--commands-file",
        type=Path,
        help="UTF-8 file containing one client command per line.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help=(
            "Additional pause after each submitted command in seconds, applied on top "
            "of the readiness handshake (default: 0.05)."
        ),
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=0.25,
        help=(
            "How long the client's output must stay silent before the next command is "
            "submitted, in seconds (default: 0.25)."
        ),
    )
    parser.add_argument(
        "--ready-timeout",
        type=float,
        default=30.0,
        help=(
            "Maximum time to wait for the client to settle before submitting a command "
            "anyway, in seconds (default: 30.0)."
        ),
    )
    parser.add_argument(
        "--no-wait-for-ready",
        action="store_true",
        help="Feed commands on --delay alone instead of waiting for the client to settle.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=180,
        help="Headless terminal width (default: 180).",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=40,
        help="Headless terminal height (default: 40).",
    )
    parser.add_argument(
        "--no-auto-exit",
        action="store_true",
        help="Do not append an exit command after the input source reaches EOF.",
    )
    parser.add_argument(
        "client_args",
        nargs=argparse.REMAINDER,
        help="Arguments after -- are forwarded to consortium.py client.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    arguments = parser.parse_args()

    if arguments.delay < 0:
        parser.error("--delay must be zero or greater")
    if arguments.settle < 0:
        parser.error("--settle must be zero or greater")
    if arguments.ready_timeout <= 0:
        parser.error("--ready-timeout must be greater than zero")
    if arguments.columns <= 0:
        parser.error("--columns must be greater than zero")
    if arguments.rows <= 0:
        parser.error("--rows must be greater than zero")

    commands = list(arguments.command)
    if arguments.commands_file is not None:
        try:
            commands.extend(_read_command_file(arguments.commands_file))
        except OSError as exc:
            parser.error(str(exc))

    command_source: Iterable[str]
    command_source = commands if commands else _stdin_commands()
    client_args = list(arguments.client_args)
    if client_args[:1] == ["--"]:
        client_args.pop(0)

    project_root = Path(__file__).resolve().parent.parent
    entrypoint = project_root / "consortium.py"
    if not entrypoint.is_file():
        parser.error(f"Consortium entry point not found: {entrypoint}")

    _configure_utf8_output()
    os.environ["COLUMNS"] = str(arguments.columns)
    os.environ["LINES"] = str(arguments.rows)
    return _run_client(
        entrypoint=entrypoint,
        client_args=client_args,
        commands=command_source,
        columns=arguments.columns,
        rows=arguments.rows,
        delay=arguments.delay,
        auto_exit=not arguments.no_auto_exit,
        settle=arguments.settle,
        ready_timeout=arguments.ready_timeout,
        wait_for_ready=not arguments.no_wait_for_ready,
    )


if __name__ == "__main__":
    raise SystemExit(main())
