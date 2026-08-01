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
"""

import argparse
import os
import runpy
import sys
import threading
import time
from collections.abc import Iterable
from pathlib import Path
from typing import TextIO

from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.data_structures import Size
from prompt_toolkit.input.base import PipeInput
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.plain_text import PlainTextOutput


class HeadlessOutput(PlainTextOutput):
    def __init__(self, stdout: TextIO, columns: int, rows: int) -> None:
        super().__init__(stdout=stdout)
        self._size = Size(rows=rows, columns=columns)

    def get_size(self) -> Size:
        return self._size


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
) -> None:
    last_command = None
    try:
        for command in commands:
            if not command.strip():
                continue
            pipe_input.send_text(f"{command}\n")
            last_command = command.strip()
            if delay:
                time.sleep(delay)

        if auto_exit and last_command != "exit":
            pipe_input.send_text("exit\n")
    except (EOFError, OSError):
        # The client may exit before all queued commands are consumed.
        return


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
) -> int:
    original_argv = sys.argv
    original_cwd = Path.cwd()
    original_sys_path = list(sys.path)
    output = HeadlessOutput(stdout=sys.stdout, columns=columns, rows=rows)

    try:
        os.chdir(entrypoint.parent)
        sys.path.insert(0, str(entrypoint.parent))
        sys.argv = [str(entrypoint), "client", *client_args]
        with create_pipe_input() as pipe_input:
            feeder = threading.Thread(
                target=_feed_commands,
                args=(pipe_input, commands, delay, auto_exit),
                daemon=True,
                name="consortium-headless-client-input",
            )
            feeder.start()
            with create_app_session(input=pipe_input, output=output):
                try:
                    runpy.run_path(str(entrypoint), run_name="__main__")
                except SystemExit as exc:
                    return _system_exit_code(exc)
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        sys.argv = original_argv
        sys.path[:] = original_sys_path
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
        help="Delay between submitted commands in seconds (default: 0.05).",
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
    )


if __name__ == "__main__":
    raise SystemExit(main())
